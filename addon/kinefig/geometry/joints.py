"""Parametric joint geometry generators for KineFig."""

from typing import Optional, Tuple, Any
import bpy
import bmesh
from mathutils import Matrix, Vector

from ..core.build_info import VERSION
from ..core.units import mm_to_blender
from ..core.validation import (
    validate_ball_joint_parameters,
    validate_double_ball_parameters,
)
from ..core.naming import get_next_object_name, format_temp_name, is_temp_object
from ..core.errors import KineFigError, KineFigGeometryError
from ..core.logging import log_info, log_error
from .boolean import evaluate_boolean_modifier


def _evaluate_boolean_union(
    context: Any, joint_obj: bpy.types.Object, mod: bpy.types.Modifier
) -> bpy.types.Mesh:
    """Internal seam: evaluates the Boolean modifier via depsgraph and returns evaluated mesh.

    This helper isolates dependency graph evaluation and mesh extraction,
    providing a safe monkeypatch seam for testing failure/rollback without
    exposing test flags in public product APIs.
    """
    return evaluate_boolean_modifier(
        context, joint_obj, mod, operation_name="Boolean union"
    )


def _evaluate_double_ball_union(
    context: Any,
    joint_obj: bpy.types.Object,
    mod: bpy.types.Modifier,
    stage: int = 1,
) -> bpy.types.Mesh:
    """Internal seam: evaluates Double Ball boolean union via depsgraph.

    Args:
        context: Blender context.
        joint_obj: The object being modified.
        mod: The Boolean modifier to evaluate.
        stage: 1 for (Ball A + Stem), 2 for ((Ball A + Stem) + Ball B).
    """
    return evaluate_boolean_modifier(
        context, joint_obj, mod, operation_name=f"Double Ball boolean union stage {stage}"
    )


def _commit_evaluated_mesh(
    eval_mesh: bpy.types.Mesh,
    target_mesh: bpy.types.Mesh,
    stage: int = 1,
) -> None:
    """Internal seam: copies geometry from evaluated mesh into target mesh datablock.

    This helper provides a safe test seam for verifying post-evaluation rollback
    without adding test flags to production APIs.
    """
    bm_copy = bmesh.new()
    try:
        bm_copy.from_mesh(eval_mesh)
        bm_copy.to_mesh(target_mesh)
    finally:
        bm_copy.free()


def create_ball_joint_geometry(
    context: Any,
    ball_diameter_mm: float = 5.0,
    stem_diameter_mm: float = 3.0,
    stem_length_mm: float = 5.0,
    segments: int = 32,
    rings: int = 16,
    location: Optional[Tuple[float, float, float]] = None,
) -> bpy.types.Object:
    """Create a parametric male ball joint (sphere + cylindrical stem) as a single manifold mesh.

    Geometry Policy:
    Produces a true boolean-unioned watertight 2-manifold mesh using Blender's
    EXACT boolean solver. Internal overlapping geometry is eliminated, ensuring
    manifoldness and 3D print readiness.

    Orientation & Origin:
    - Default location: 3D Cursor position (or specified location).
    - Local origin: (0, 0, 0) at the base of the stem.
    - Local joint axis: along +Z (from stem base towards the ball center).
    - Stem cylinder extends along +Z from z = 0 to z = stem_length_m.
    - Ball sphere is centered at (0, 0, stem_length_m).

    Transactional Safety:
    On ANY failure after scene mutation begins, all allocated resources
    (objects, meshes, modifiers) are deterministically cleaned up before
    raising KineFigGeometryError. Unrelated scene state is never modified.

    Returns:
        The created KineFig joint object (e.g. KF_Joint_Ball_001).
    """
    # 1. Validate parameters (fails cleanly before any scene mutation)
    validate_ball_joint_parameters(
        ball_diameter_mm=ball_diameter_mm,
        stem_diameter_mm=stem_diameter_mm,
        stem_length_mm=stem_length_mm,
        segments=segments,
        rings=rings,
    )

    # 2. Convert millimeters to Blender standard units (1 BU = 1 meter)
    ball_diameter_m = mm_to_blender(ball_diameter_mm)
    ball_radius_m = ball_diameter_m / 2.0
    stem_diameter_m = mm_to_blender(stem_diameter_mm)
    stem_radius_m = stem_diameter_m / 2.0
    stem_length_m = mm_to_blender(stem_length_mm)

    collection = (
        context.collection
        if hasattr(context, "collection") and context.collection
        else (context.scene.collection if hasattr(context, "scene") else None)
    )

    # Track allocated resources for transactional rollback
    joint_obj: Optional[bpy.types.Object] = None
    sphere_mesh: Optional[bpy.types.Mesh] = None
    temp_stem_obj: Optional[bpy.types.Object] = None
    temp_stem_mesh: Optional[bpy.types.Mesh] = None
    eval_mesh: Optional[bpy.types.Mesh] = None
    mod: Optional[bpy.types.Modifier] = None

    try:
        # 3. Create initial sphere mesh datablock with guarded BMesh lifecycle
        sphere_mesh = bpy.data.meshes.new("KF_Joint_Ball_Mesh")
        bm_sphere = bmesh.new()
        try:
            bmesh.ops.create_uvsphere(
                bm_sphere,
                u_segments=int(segments),
                v_segments=int(rings),
                radius=ball_radius_m,
            )
            bmesh.ops.translate(
                bm_sphere,
                vec=(0.0, 0.0, stem_length_m),
                verts=bm_sphere.verts,
            )
            bm_sphere.to_mesh(sphere_mesh)
        finally:
            bm_sphere.free()

        # 4. Allocate deterministic object name
        existing_names = [o.name for o in bpy.data.objects]
        object_name = get_next_object_name("Joint", detail="Ball", existing_names=existing_names)
        joint_obj = bpy.data.objects.new(object_name, sphere_mesh)

        # 5. Create temporary stem cylinder with guarded BMesh lifecycle
        temp_mesh_name = format_temp_name("Stem_Mesh")
        temp_stem_mesh = bpy.data.meshes.new(temp_mesh_name)
        bm_cyl = bmesh.new()
        try:
            bmesh.ops.create_cone(
                bm_cyl,
                cap_ends=True,
                segments=int(segments),
                radius1=stem_radius_m,
                radius2=stem_radius_m,
                depth=stem_length_m,
            )
            bmesh.ops.translate(
                bm_cyl,
                vec=(0.0, 0.0, stem_length_m / 2.0),
                verts=bm_cyl.verts,
            )
            bm_cyl.to_mesh(temp_stem_mesh)
        finally:
            bm_cyl.free()

        temp_obj_name = format_temp_name("Stem_Obj")
        temp_stem_obj = bpy.data.objects.new(temp_obj_name, temp_stem_mesh)

        # Link both objects to active collection for boolean resolution
        if collection:
            collection.objects.link(joint_obj)
            collection.objects.link(temp_stem_obj)

        # 6. Apply Exact Boolean Union
        mod = joint_obj.modifiers.new(name="KF_Union_Stem", type="BOOLEAN")
        mod.operation = "UNION"
        mod.object = temp_stem_obj
        mod.solver = "EXACT"

        # Evaluate modifier through internal seam
        eval_mesh = _evaluate_boolean_union(context, joint_obj, mod)

        # Verified evaluated mesh: now commit to joint_obj
        joint_obj.modifiers.remove(mod)
        mod = None
        joint_obj.data = eval_mesh

        # Clean up original sphere mesh now that evaluated mesh is committed
        bpy.data.meshes.remove(sphere_mesh, do_unlink=True)
        sphere_mesh = None

        # Clean up temporary stem objects
        if collection and hasattr(collection, "objects") and temp_stem_obj.name in collection.objects:
            collection.objects.unlink(temp_stem_obj)
        bpy.data.objects.remove(temp_stem_obj, do_unlink=True)
        temp_stem_obj = None

        bpy.data.meshes.remove(temp_stem_mesh, do_unlink=True)
        temp_stem_mesh = None

        # 7. Verify postconditions before returning
        if joint_obj.data is None:
            raise KineFigGeometryError("Postcondition failed: joint object has no valid mesh data")
        if any(m.type == "BOOLEAN" for m in joint_obj.modifiers):
            raise KineFigGeometryError("Postcondition failed: dangling Boolean modifier on joint object")
        if is_temp_object(joint_obj.name):
            raise KineFigGeometryError(f"Postcondition failed: joint object has temporary name {joint_obj.name}")

        # 8. Set creation transform
        if location is not None:
            joint_obj.location = location
        elif hasattr(context, "scene") and hasattr(context.scene, "cursor"):
            joint_obj.location = context.scene.cursor.location

        # 9. Set factual KineFig parametric metadata only (omit uncomputed/unknown keys)
        joint_obj["kf_type"] = "joint"
        joint_obj["kf_joint_type"] = "ball"
        joint_obj["kf_version"] = VERSION
        joint_obj["kf_ball_diameter_mm"] = float(ball_diameter_mm)
        joint_obj["kf_stem_diameter_mm"] = float(stem_diameter_mm)
        joint_obj["kf_stem_length_mm"] = float(stem_length_mm)
        joint_obj["kf_axis"] = (0.0, 0.0, 1.0)

        # 10. Log operational event
        log_info(
            f"Created male Ball Joint: {joint_obj.name}",
            name=joint_obj.name,
            ball_diameter_mm=ball_diameter_mm,
            stem_diameter_mm=stem_diameter_mm,
            stem_length_mm=stem_length_mm,
        )

        return joint_obj

    except Exception as exc:
        # Transactional rollback: Clean up all resources created during this operation
        if collection and hasattr(collection, "objects"):
            if temp_stem_obj and temp_stem_obj.name in collection.objects:
                try:
                    collection.objects.unlink(temp_stem_obj)
                except Exception:
                    pass
            if joint_obj and joint_obj.name in collection.objects:
                try:
                    collection.objects.unlink(joint_obj)
                except Exception:
                    pass

        if temp_stem_obj and hasattr(bpy.data, "objects"):
            try:
                bpy.data.objects.remove(temp_stem_obj, do_unlink=True)
            except Exception:
                pass

        if joint_obj and hasattr(bpy.data, "objects"):
            try:
                bpy.data.objects.remove(joint_obj, do_unlink=True)
            except Exception:
                pass

        if temp_stem_mesh and hasattr(bpy.data, "meshes"):
            try:
                bpy.data.meshes.remove(temp_stem_mesh, do_unlink=True)
            except Exception:
                pass

        if eval_mesh and hasattr(bpy.data, "meshes"):
            try:
                bpy.data.meshes.remove(eval_mesh, do_unlink=True)
            except Exception:
                pass

        if sphere_mesh and hasattr(bpy.data, "meshes"):
            try:
                bpy.data.meshes.remove(sphere_mesh, do_unlink=True)
            except Exception:
                pass

        log_error(f"create_ball_joint_geometry failed and rolled back cleanly: {exc}")

        if isinstance(exc, KineFigError):
            raise
        raise KineFigGeometryError(f"Failed to create ball joint geometry: {exc}") from exc


def create_double_ball_geometry(
    context: Any,
    ball_a_diameter_mm: float = 5.0,
    ball_b_diameter_mm: float = 5.0,
    stem_diameter_mm: float = 3.0,
    center_distance_mm: float = 8.0,
    segments: int = 32,
    rings: int = 16,
    location: Optional[Tuple[float, float, float]] = None,
) -> bpy.types.Object:
    """Create a parametric Double Ball / Dumbbell Joint as a single coherent manifold solid.

    Geometry Policy:
    Produces a single coherent watertight 2-manifold mesh using Blender's
    EXACT boolean solver. Combines Ball A at origin, connecting cylindrical stem
    along +Z, and Ball B at (0, 0, center_distance_mm). Internal overlapping geometry
    is eliminated via two-stage boolean union, ensuring print readiness.

    Orientation & Coordinates:
    - Canonical axis: +Z (kf_axis = (0.0, 0.0, 1.0)).
    - Ball A center: (0, 0, 0) at local origin.
    - Ball B center: (0, 0, center_distance_mm) along +Z.
    - Total height: from -ball_a_radius to +(center_distance + ball_b_radius).
    - Center distance: distance between Ball A and Ball B centers.

    Transactional Safety:
    Multi-stage rollback ensures that on ANY failure during primitive creation,
    Stage 1 union, or Stage 2 union, all allocated resources (objects, meshes,
    modifiers) are deterministically cleaned up before raising KineFigGeometryError.
    Unrelated scene state is never modified.
    """
    validate_double_ball_parameters(
        ball_a_diameter_mm=ball_a_diameter_mm,
        ball_b_diameter_mm=ball_b_diameter_mm,
        stem_diameter_mm=stem_diameter_mm,
        center_distance_mm=center_distance_mm,
        segments=segments,
        rings=rings,
    )

    if context is None:
        raise KineFigGeometryError("Blender context is required to create joint geometry")

    r_a_m = mm_to_blender(ball_a_diameter_mm / 2.0)
    r_b_m = mm_to_blender(ball_b_diameter_mm / 2.0)
    r_stem_m = mm_to_blender(stem_diameter_mm / 2.0)
    dist_m = mm_to_blender(center_distance_mm)

    existing_names = [o.name for o in bpy.data.objects] if hasattr(bpy.data, "objects") else []
    joint_obj_name = get_next_object_name("Joint", detail="DoubleBall", existing_names=existing_names)
    joint_mesh_name = f"{joint_obj_name}_Mesh"
    temp_stem_name = format_temp_name(f"{joint_obj_name}_Stem")
    temp_ball_b_name = format_temp_name(f"{joint_obj_name}_BallB")

    created_objects = []
    created_meshes = []
    eval_mesh_1 = None
    eval_mesh_2 = None

    target_col = None
    if hasattr(context, "collection") and context.collection is not None:
        target_col = context.collection
    elif hasattr(context, "scene") and hasattr(context.scene, "collection"):
        target_col = context.scene.collection

    try:
        # 1. Create Ball A primitive centered at local origin (0, 0, 0)
        bm_a = bmesh.new()
        try:
            bmesh.ops.create_uvsphere(
                bm_a,
                u_segments=segments,
                v_segments=rings,
                radius=r_a_m,
            )
            joint_mesh = bpy.data.meshes.new(name=joint_mesh_name)
            created_meshes.append(joint_mesh)
            bm_a.to_mesh(joint_mesh)
        finally:
            bm_a.free()

        joint_obj = bpy.data.objects.new(joint_obj_name, joint_mesh)
        created_objects.append(joint_obj)
        if target_col is not None:
            target_col.objects.link(joint_obj)

        # 2. Create connecting stem cylinder along +Z from z = 0 to z = dist_m
        bm_stem = bmesh.new()
        try:
            mat_stem = Matrix.Translation(Vector((0.0, 0.0, dist_m / 2.0)))
            bmesh.ops.create_cone(
                bm_stem,
                cap_ends=True,
                cap_tris=False,
                segments=segments,
                radius1=r_stem_m,
                radius2=r_stem_m,
                depth=dist_m,
                matrix=mat_stem,
            )
            temp_stem_mesh = bpy.data.meshes.new(name=f"{temp_stem_name}_Mesh")
            created_meshes.append(temp_stem_mesh)
            bm_stem.to_mesh(temp_stem_mesh)
        finally:
            bm_stem.free()

        temp_stem_obj = bpy.data.objects.new(temp_stem_name, temp_stem_mesh)
        created_objects.append(temp_stem_obj)
        if target_col is not None:
            target_col.objects.link(temp_stem_obj)

        # 3. Stage 1 Boolean Union: Ball A + Stem
        mod_stem = joint_obj.modifiers.new(name="KF_Union_Stem", type='BOOLEAN')
        mod_stem.operation = 'UNION'
        mod_stem.solver = 'EXACT'
        mod_stem.object = temp_stem_obj

        eval_mesh_1 = _evaluate_double_ball_union(context, joint_obj, mod_stem, stage=1)
        created_meshes.append(eval_mesh_1)

        # Remove Stage 1 modifier and temporary stem object
        joint_obj.modifiers.remove(mod_stem)
        if target_col is not None and temp_stem_obj.name in target_col.objects:
            target_col.objects.unlink(temp_stem_obj)
        if temp_stem_obj.name in bpy.data.objects:
            bpy.data.objects.remove(temp_stem_obj, do_unlink=True)
        if temp_stem_obj in created_objects:
            created_objects.remove(temp_stem_obj)
        if temp_stem_mesh.name in bpy.data.meshes:
            bpy.data.meshes.remove(temp_stem_mesh, do_unlink=True)
        if temp_stem_mesh in created_meshes:
            created_meshes.remove(temp_stem_mesh)

        # Commit Stage 1 evaluated mesh
        stage1_mesh = bpy.data.meshes.new(name=f"{joint_mesh_name}_Stage1")
        created_meshes.append(stage1_mesh)

        _commit_evaluated_mesh(eval_mesh_1, stage1_mesh, stage=1)

        # Explicitly remove eval_mesh_1 once safely committed
        if eval_mesh_1 in created_meshes:
            created_meshes.remove(eval_mesh_1)
        if hasattr(eval_mesh_1, "name") and eval_mesh_1.name in bpy.data.meshes:
            bpy.data.meshes.remove(eval_mesh_1, do_unlink=True)
        eval_mesh_1 = None

        # Swap joint_obj data to stage1_mesh and remove initial sphere mesh
        joint_obj.data = stage1_mesh
        if joint_mesh.name in bpy.data.meshes:
            bpy.data.meshes.remove(joint_mesh, do_unlink=True)
        if joint_mesh in created_meshes:
            created_meshes.remove(joint_mesh)

        # 4. Create Ball B primitive centered at (0, 0, dist_m)
        bm_b = bmesh.new()
        try:
            mat_b = Matrix.Translation(Vector((0.0, 0.0, dist_m)))
            bmesh.ops.create_uvsphere(
                bm_b,
                u_segments=segments,
                v_segments=rings,
                radius=r_b_m,
                matrix=mat_b,
            )
            temp_ball_b_mesh = bpy.data.meshes.new(name=f"{temp_ball_b_name}_Mesh")
            created_meshes.append(temp_ball_b_mesh)
            bm_b.to_mesh(temp_ball_b_mesh)
        finally:
            bm_b.free()

        temp_ball_b_obj = bpy.data.objects.new(temp_ball_b_name, temp_ball_b_mesh)
        created_objects.append(temp_ball_b_obj)
        if target_col is not None:
            target_col.objects.link(temp_ball_b_obj)

        # 5. Stage 2 Boolean Union: (Ball A + Stem) + Ball B
        mod_ball_b = joint_obj.modifiers.new(name="KF_Union_BallB", type='BOOLEAN')
        mod_ball_b.operation = 'UNION'
        mod_ball_b.solver = 'EXACT'
        mod_ball_b.object = temp_ball_b_obj

        eval_mesh_2 = _evaluate_double_ball_union(context, joint_obj, mod_ball_b, stage=2)
        created_meshes.append(eval_mesh_2)

        # Remove Stage 2 modifier and temporary Ball B object
        joint_obj.modifiers.remove(mod_ball_b)
        if target_col is not None and temp_ball_b_obj.name in target_col.objects:
            target_col.objects.unlink(temp_ball_b_obj)
        if temp_ball_b_obj.name in bpy.data.objects:
            bpy.data.objects.remove(temp_ball_b_obj, do_unlink=True)
        if temp_ball_b_obj in created_objects:
            created_objects.remove(temp_ball_b_obj)
        if temp_ball_b_mesh.name in bpy.data.meshes:
            bpy.data.meshes.remove(temp_ball_b_mesh, do_unlink=True)
        if temp_ball_b_mesh in created_meshes:
            created_meshes.remove(temp_ball_b_mesh)

        # Commit final clean mesh
        final_mesh = bpy.data.meshes.new(name=joint_mesh_name)
        created_meshes.append(final_mesh)

        _commit_evaluated_mesh(eval_mesh_2, final_mesh, stage=2)

        # Explicitly remove eval_mesh_2 once safely committed
        if eval_mesh_2 in created_meshes:
            created_meshes.remove(eval_mesh_2)
        if hasattr(eval_mesh_2, "name") and eval_mesh_2.name in bpy.data.meshes:
            bpy.data.meshes.remove(eval_mesh_2, do_unlink=True)
        eval_mesh_2 = None

        # Swap joint_obj data to final_mesh and remove stage1_mesh
        joint_obj.data = final_mesh
        if stage1_mesh.name in bpy.data.meshes:
            bpy.data.meshes.remove(stage1_mesh, do_unlink=True)
        if stage1_mesh in created_meshes:
            created_meshes.remove(stage1_mesh)

        # 6. Apply transforms and location (3D Cursor or specified location)
        if location is not None:
            joint_obj.location = location
        elif hasattr(context, "scene") and hasattr(context.scene, "cursor"):
            joint_obj.location = context.scene.cursor.location

        # 7. Set factual KineFig parametric metadata only
        joint_obj["kf_type"] = "joint"
        joint_obj["kf_joint_type"] = "double_ball"
        joint_obj["kf_version"] = VERSION
        joint_obj["kf_ball_a_diameter_mm"] = round(float(ball_a_diameter_mm), 4)
        joint_obj["kf_ball_b_diameter_mm"] = round(float(ball_b_diameter_mm), 4)
        joint_obj["kf_stem_diameter_mm"] = round(float(stem_diameter_mm), 4)
        joint_obj["kf_center_distance_mm"] = round(float(center_distance_mm), 4)
        joint_obj["kf_axis"] = (0.0, 0.0, 1.0)
        joint_obj["kf_ball_a_center_mm"] = (0.0, 0.0, 0.0)
        joint_obj["kf_ball_b_center_mm"] = (0.0, 0.0, round(float(center_distance_mm), 4))

        # 8. Log operational event
        log_info(
            f"Created Double Ball joint: {joint_obj.name}",
            name=joint_obj.name,
            ball_a_diameter_mm=ball_a_diameter_mm,
            ball_b_diameter_mm=ball_b_diameter_mm,
            stem_diameter_mm=stem_diameter_mm,
            center_distance_mm=center_distance_mm,
        )

        return joint_obj

    except Exception as exc:
        # Clean up any leftover modifiers on joint_obj
        for obj in list(created_objects):
            try:
                for mod in list(obj.modifiers):
                    obj.modifiers.remove(mod)
            except Exception:
                pass

        # Transactional rollback: remove all newly created objects
        for obj in list(created_objects):
            try:
                for col in bpy.data.collections:
                    if obj.name in col.objects:
                        col.objects.unlink(obj)
                if hasattr(bpy.context, "scene") and hasattr(bpy.context.scene, "collection"):
                    if obj.name in bpy.context.scene.collection.objects:
                        bpy.context.scene.collection.objects.unlink(obj)
                if obj.name in bpy.data.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
            except Exception:
                pass

        # Transactional rollback: remove any uncommitted evaluated meshes
        for em in (eval_mesh_1, eval_mesh_2):
            if em is not None:
                try:
                    if hasattr(em, "name") and em.name in bpy.data.meshes:
                        bpy.data.meshes.remove(em, do_unlink=True)
                except Exception:
                    pass

        # Transactional rollback: remove all newly created meshes
        for mesh in list(created_meshes):
            try:
                if mesh and hasattr(mesh, "name") and mesh.name in bpy.data.meshes:
                    bpy.data.meshes.remove(mesh, do_unlink=True)
            except Exception:
                pass

        log_error(f"create_double_ball_geometry failed and rolled back cleanly: {exc}")

        if isinstance(exc, KineFigError):
            raise
        raise KineFigGeometryError(f"Failed to create double ball joint geometry: {exc}") from exc

