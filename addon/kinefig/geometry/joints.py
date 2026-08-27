"""Parametric joint geometry generators for KineFig."""

import math
from typing import Optional, Tuple, Any
import bpy
import bmesh

from ..core.build_info import VERSION
from ..core.units import mm_to_blender, get_scene_scale_length
from ..core.validation import validate_ball_joint_parameters, validate_peg_parameters
from ..core.naming import get_next_object_name, format_temp_name, is_temp_object
from ..core.errors import KineFigError, KineFigGeometryError
from ..core.logging import log_info, log_error


def _evaluate_boolean_union(
    context: Any, joint_obj: bpy.types.Object, mod: bpy.types.Modifier
) -> bpy.types.Mesh:
    """Internal seam: evaluates the Boolean modifier via depsgraph and returns evaluated mesh.

    This helper isolates dependency graph evaluation and mesh extraction,
    providing a safe monkeypatch seam for testing failure/rollback without
    exposing test flags in public product APIs.
    """
    if not hasattr(context, "evaluated_depsgraph_get"):
        raise KineFigGeometryError("Context has no evaluated_depsgraph_get method")

    depsgraph = context.evaluated_depsgraph_get()
    eval_obj = joint_obj.evaluated_get(depsgraph)
    eval_mesh = bpy.data.meshes.new_from_object(eval_obj)

    if eval_mesh is None:
        raise KineFigGeometryError("Boolean union failed to generate evaluated mesh")

    try:
        vert_count = len(eval_mesh.vertices)
    except (TypeError, AttributeError):
        raise KineFigGeometryError("Evaluated mesh has invalid or missing vertices attribute")

    if vert_count == 0:
        raise KineFigGeometryError("Boolean union produced empty mesh geometry (0 vertices)")

    return eval_mesh


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

    # 2. Convert millimeters to Blender internal units (BU) respecting scene scale_length
    scale_length = get_scene_scale_length(context)
    ball_diameter_m = mm_to_blender(ball_diameter_mm, scale_length)
    ball_radius_m = ball_diameter_m / 2.0
    stem_diameter_m = mm_to_blender(stem_diameter_mm, scale_length)
    stem_radius_m = stem_diameter_m / 2.0
    stem_length_m = mm_to_blender(stem_length_mm, scale_length)

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


def create_peg_geometry(
    context: Any,
    peg_diameter_mm: float = 3.0,
    peg_length_mm: float = 5.0,
    taper_angle_deg: float = 0.0,
    segments: int = 32,
    location: Optional[Tuple[float, float, float]] = None,
) -> bpy.types.Object:
    """Create a parametric male cylindrical peg connector as a single manifold mesh.

    Geometry Policy:
    Produces a single coherent, watertight 2-manifold solid cylinder (or conical frustum
    if tapered) aligned along canonical local +Z. The peg base is at local z = 0 and
    extends along +Z to z = +peg_length_mm.

    Orientation & Origin:
    - Default location: 3D Cursor position (or specified location).
    - Local origin: (0, 0, 0) at the center of the peg base plane.
    - Local joint axis (kf_axis): (0.0, 0.0, 1.0) pointing from base towards insertion tip.
    - Base plane: z = 0 (exact nominal diameter = peg_diameter_mm).
    - Insertion tip: z = +peg_length_mm.

    Transactional Safety:
    On ANY failure after scene mutation begins, all allocated resources are
    deterministically cleaned up before raising KineFigGeometryError.

    Returns:
        The created KineFig joint object (e.g. KF_Joint_Peg_001).
    """
    validate_peg_parameters(
        peg_diameter_mm=peg_diameter_mm,
        peg_length_mm=peg_length_mm,
        taper_angle_deg=taper_angle_deg,
        segments=segments,
    )

    if context is None:
        raise KineFigGeometryError("Blender context is required to create peg geometry")

    scale_length = get_scene_scale_length(context)
    r_base_m = mm_to_blender(peg_diameter_mm / 2.0, scale_length)
    length_m = mm_to_blender(peg_length_mm, scale_length)
    taper_rad = math.radians(float(taper_angle_deg))
    r_tip_m = r_base_m - length_m * math.tan(taper_rad)

    collection = (
        context.collection
        if hasattr(context, "collection") and context.collection
        else (context.scene.collection if hasattr(context, "scene") else None)
    )

    existing_names = [o.name for o in bpy.data.objects] if hasattr(bpy.data, "objects") else []
    object_name = get_next_object_name("Joint", detail="Peg", existing_names=existing_names)
    mesh_name = f"{object_name}_Mesh"

    created_objects = []
    created_meshes = []

    try:
        peg_mesh = bpy.data.meshes.new(mesh_name)
        created_meshes.append(peg_mesh)

        bm = bmesh.new()
        try:
            bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                segments=int(segments),
                radius1=r_base_m,
                radius2=r_tip_m,
                depth=length_m,
            )
            bmesh.ops.translate(
                bm,
                vec=(0.0, 0.0, length_m / 2.0),
                verts=bm.verts,
            )
            bm.to_mesh(peg_mesh)
        finally:
            bm.free()

        peg_obj = bpy.data.objects.new(object_name, peg_mesh)
        created_objects.append(peg_obj)

        if collection and hasattr(collection, "objects"):
            collection.objects.link(peg_obj)

        # Set location
        if location is not None:
            peg_obj.location = location
        elif hasattr(context, "scene") and hasattr(context.scene, "cursor"):
            peg_obj.location = context.scene.cursor.location

        # Set factual KineFig metadata only
        peg_obj["kf_type"] = "joint"
        peg_obj["kf_joint_type"] = "peg"
        peg_obj["kf_version"] = VERSION
        peg_obj["kf_peg_diameter_mm"] = round(float(peg_diameter_mm), 4)
        peg_obj["kf_peg_length_mm"] = round(float(peg_length_mm), 4)
        peg_obj["kf_taper_angle_deg"] = round(float(taper_angle_deg), 4)
        peg_obj["kf_axis"] = (0.0, 0.0, 1.0)

        log_info(
            f"Created Peg joint: {peg_obj.name}",
            name=peg_obj.name,
            peg_diameter_mm=peg_diameter_mm,
            peg_length_mm=peg_length_mm,
            taper_angle_deg=taper_angle_deg,
        )

        return peg_obj

    except Exception as exc:
        if collection and hasattr(collection, "objects"):
            for obj in list(created_objects):
                if obj.name in collection.objects:
                    try:
                        collection.objects.unlink(obj)
                    except Exception:
                        pass

        for obj in list(created_objects):
            if hasattr(bpy.data, "objects") and obj.name in bpy.data.objects:
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                except Exception:
                    pass

        for mesh in list(created_meshes):
            if hasattr(bpy.data, "meshes") and mesh.name in bpy.data.meshes:
                try:
                    bpy.data.meshes.remove(mesh, do_unlink=True)
                except Exception:
                    pass

        log_error(f"create_peg_geometry failed and rolled back cleanly: {exc}")

        if isinstance(exc, KineFigError):
            raise
        raise KineFigGeometryError(f"Failed to create peg joint geometry: {exc}") from exc

