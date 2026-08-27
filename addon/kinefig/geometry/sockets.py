"""Parametric socket cavity geometry generators for KineFig."""

from typing import Optional, Tuple, Any
import bpy
import bmesh

from ..core.build_info import VERSION
from ..core.units import mm_to_blender, get_scene_scale_length
from ..core.clearance import compute_socket_diameter
from ..core.validation import validate_ball_socket_parameters, validate_peg_socket_parameters
from ..core.naming import get_next_object_name, format_temp_name, is_temp_object
from ..core.errors import KineFigError, KineFigGeometryError
from ..core.logging import log_info, log_error


def _evaluate_boolean_trim(
    context: Any, socket_obj: bpy.types.Object, mod: bpy.types.Modifier
) -> bpy.types.Mesh:
    """Internal seam: evaluates the Boolean trimming modifier via depsgraph and returns evaluated mesh.

    This helper isolates dependency graph evaluation and mesh extraction,
    providing a safe monkeypatch seam for testing failure/rollback without
    exposing test flags in public product APIs.
    """
    if not hasattr(context, "evaluated_depsgraph_get"):
        raise KineFigGeometryError("Context has no evaluated_depsgraph_get method")

    depsgraph = context.evaluated_depsgraph_get()
    eval_obj = socket_obj.evaluated_get(depsgraph)
    eval_mesh = bpy.data.meshes.new_from_object(eval_obj)

    if eval_mesh is None:
        raise KineFigGeometryError("Boolean trimming failed to generate evaluated mesh")

    try:
        vert_count = len(eval_mesh.vertices)
    except (TypeError, AttributeError):
        raise KineFigGeometryError("Evaluated mesh has invalid or missing vertices attribute")

    if vert_count == 0:
        raise KineFigGeometryError("Boolean trimming produced empty mesh geometry (0 vertices)")

    return eval_mesh


def create_ball_socket_geometry(
    context: Any,
    ball_diameter_mm: float = 5.0,
    clearance_mm: float = 0.15,
    socket_depth_mm: float = 3.5,
    segments: int = 32,
    rings: int = 16,
    location: Optional[Tuple[float, float, float]] = None,
) -> bpy.types.Object:
    """Create a parametric female ball socket cavity tool as a closed watertight 2-manifold mesh.

    Geometry Policy:
    Generates a solid cutter/cavity volume representing the negative space of the
    socket. The spherical cavity is trimmed cleanly at the insertion plane z = 0
    using Blender's EXACT boolean difference solver, producing a watertight,
    closed 2-manifold volume with a planar circular opening cap.

    Clearance Contract:
    Radial clearance is applied uniformly:
        socket_diameter = ball_diameter + 2 * clearance

    Orientation & Coordinates:
    - Default location: 3D Cursor position (or specified location).
    - Local origin: (0, 0, 0) at the center of the planar opening face.
    - Socket cavity axis (kf_axis): along +Z (cavity extends from z = 0 to z = socket_depth_m).
    - Deepest internal cavity point: at (0, 0, socket_depth_m).
    - Insertion direction (kf_insertion_axis): (0.0, 0.0, 1.0) (male ball travel from outside into cavity).
    - Opening outward normal (kf_opening_normal): (0.0, 0.0, -1.0) (pointing outward from opening plane).
    - Sphere center: at (0, 0, socket_depth_m - socket_radius_m).

    Transactional Safety:
    On ANY failure after scene mutation begins, all allocated resources
    (objects, meshes, modifiers) are deterministically cleaned up before
    raising KineFigGeometryError. Unrelated scene state is never modified.

    Returns:
        The created KineFig socket object (e.g. KF_Socket_Ball_001).
    """
    # 1. Validate parameters (fails cleanly before any scene mutation)
    validate_ball_socket_parameters(
        ball_diameter_mm=ball_diameter_mm,
        clearance_mm=clearance_mm,
        socket_depth_mm=socket_depth_mm,
        segments=segments,
        rings=rings,
    )

    # 2. Convert millimeters to Blender internal units (BU) respecting scene scale_length
    scale_length = get_scene_scale_length(context)
    socket_diameter_mm = compute_socket_diameter(ball_diameter_mm, clearance_mm)
    socket_diameter_m = mm_to_blender(socket_diameter_mm, scale_length)
    socket_radius_m = socket_diameter_m / 2.0
    socket_depth_m = mm_to_blender(socket_depth_mm, scale_length)

    # Center of sphere along Z such that highest point is at socket_depth_m
    z_center_m = socket_depth_m - socket_radius_m

    collection = (
        context.collection
        if hasattr(context, "collection") and context.collection
        else (context.scene.collection if hasattr(context, "scene") else None)
    )

    # Track allocated resources for transactional rollback
    socket_obj: Optional[bpy.types.Object] = None
    sphere_mesh: Optional[bpy.types.Mesh] = None
    temp_box_obj: Optional[bpy.types.Object] = None
    temp_box_mesh: Optional[bpy.types.Mesh] = None
    eval_mesh: Optional[bpy.types.Mesh] = None
    mod: Optional[bpy.types.Modifier] = None

    try:
        # 3. Create initial sphere mesh datablock with guarded BMesh lifecycle
        sphere_mesh = bpy.data.meshes.new("KF_Socket_Ball_Mesh")
        bm_sphere = bmesh.new()
        try:
            bmesh.ops.create_uvsphere(
                bm_sphere,
                u_segments=int(segments),
                v_segments=int(rings),
                radius=socket_radius_m,
            )
            bmesh.ops.translate(
                bm_sphere,
                vec=(0.0, 0.0, z_center_m),
                verts=bm_sphere.verts,
            )
            bm_sphere.to_mesh(sphere_mesh)
        finally:
            bm_sphere.free()

        # 4. Allocate deterministic object name
        existing_names = [o.name for o in bpy.data.objects]
        object_name = get_next_object_name("Socket", detail="Ball", existing_names=existing_names)
        socket_obj = bpy.data.objects.new(object_name, sphere_mesh)

        # 5. Create temporary trimming box covering z < 0 with guarded BMesh lifecycle
        temp_mesh_name = format_temp_name("Trim_Box_Mesh")
        temp_box_mesh = bpy.data.meshes.new(temp_mesh_name)
        bm_box = bmesh.new()

        box_width_m = socket_diameter_m * 3.0
        box_depth_m = socket_diameter_m * 2.0

        try:
            bmesh.ops.create_cube(
                bm_box,
                size=1.0,
            )
            # Scale cube to desired dimensions
            bmesh.ops.scale(
                bm_box,
                vec=(box_width_m, box_width_m, box_depth_m),
                verts=bm_box.verts,
            )
            # Position so top face is at z = 0.0, extending into negative Z
            bmesh.ops.translate(
                bm_box,
                vec=(0.0, 0.0, -box_depth_m / 2.0),
                verts=bm_box.verts,
            )
            bm_box.to_mesh(temp_box_mesh)
        finally:
            bm_box.free()

        temp_obj_name = format_temp_name("Trim_Box_Obj")
        temp_box_obj = bpy.data.objects.new(temp_obj_name, temp_box_mesh)

        # Link both objects to active collection for boolean resolution
        if collection:
            collection.objects.link(socket_obj)
            collection.objects.link(temp_box_obj)

        # 6. Apply Exact Boolean Difference to slice sphere at z = 0
        mod = socket_obj.modifiers.new(name="KF_Trim_Opening", type="BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = temp_box_obj
        mod.solver = "EXACT"

        # Evaluate modifier through internal seam
        eval_mesh = _evaluate_boolean_trim(context, socket_obj, mod)

        # Verified evaluated mesh: now commit to socket_obj
        socket_obj.modifiers.remove(mod)
        mod = None
        socket_obj.data = eval_mesh

        # Clean up original sphere mesh now that evaluated mesh is committed
        bpy.data.meshes.remove(sphere_mesh, do_unlink=True)
        sphere_mesh = None

        # Clean up temporary trimming box objects
        if collection and hasattr(collection, "objects") and temp_box_obj.name in collection.objects:
            collection.objects.unlink(temp_box_obj)
        bpy.data.objects.remove(temp_box_obj, do_unlink=True)
        temp_box_obj = None

        bpy.data.meshes.remove(temp_box_mesh, do_unlink=True)
        temp_box_mesh = None

        # 7. Verify postconditions before returning
        if socket_obj.data is None:
            raise KineFigGeometryError("Postcondition failed: socket object has no valid mesh data")
        if any(m.type == "BOOLEAN" for m in socket_obj.modifiers):
            raise KineFigGeometryError("Postcondition failed: dangling Boolean modifier on socket object")
        if is_temp_object(socket_obj.name):
            raise KineFigGeometryError(f"Postcondition failed: socket object has temporary name {socket_obj.name}")

        # 8. Set creation transform
        if location is not None:
            socket_obj.location = location
        elif hasattr(context, "scene") and hasattr(context.scene, "cursor"):
            socket_obj.location = context.scene.cursor.location

        # 9. Set factual KineFig parametric metadata only (omit uncomputed/unknown keys)
        socket_obj["kf_type"] = "socket"
        socket_obj["kf_socket_type"] = "ball"
        socket_obj["kf_version"] = VERSION
        socket_obj["kf_ball_diameter_mm"] = round(float(ball_diameter_mm), 4)
        socket_obj["kf_clearance_mm"] = round(float(clearance_mm), 4)
        socket_obj["kf_socket_diameter_mm"] = round(float(socket_diameter_mm), 4)
        socket_obj["kf_socket_depth_mm"] = round(float(socket_depth_mm), 4)
        socket_obj["kf_axis"] = (0.0, 0.0, 1.0)
        socket_obj["kf_insertion_axis"] = (0.0, 0.0, 1.0)
        socket_obj["kf_opening_normal"] = (0.0, 0.0, -1.0)

        # 10. Log operational event
        log_info(
            f"Created female Ball Socket: {socket_obj.name}",
            name=socket_obj.name,
            ball_diameter_mm=ball_diameter_mm,
            clearance_mm=clearance_mm,
            socket_diameter_mm=socket_diameter_mm,
            socket_depth_mm=socket_depth_mm,
        )

        return socket_obj

    except Exception as exc:
        # Transactional rollback: Clean up all resources created during this operation
        if collection and hasattr(collection, "objects"):
            if temp_box_obj and temp_box_obj.name in collection.objects:
                try:
                    collection.objects.unlink(temp_box_obj)
                except Exception:
                    pass
            if socket_obj and socket_obj.name in collection.objects:
                try:
                    collection.objects.unlink(socket_obj)
                except Exception:
                    pass

        if temp_box_obj and hasattr(bpy.data, "objects"):
            try:
                bpy.data.objects.remove(temp_box_obj, do_unlink=True)
            except Exception:
                pass

        if socket_obj and hasattr(bpy.data, "objects"):
            try:
                bpy.data.objects.remove(socket_obj, do_unlink=True)
            except Exception:
                pass

        if temp_box_mesh and hasattr(bpy.data, "meshes"):
            try:
                bpy.data.meshes.remove(temp_box_mesh, do_unlink=True)
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

        log_error(f"create_ball_socket_geometry failed and rolled back cleanly: {exc}")

        if isinstance(exc, KineFigError):
            raise
        raise KineFigGeometryError(f"Failed to create ball socket geometry: {exc}") from exc


def create_peg_socket_geometry(
    context: Any,
    peg_diameter_mm: float = 3.0,
    radial_clearance_mm: float = 0.15,
    socket_depth_mm: float = 5.0,
    segments: int = 32,
    location: Optional[Tuple[float, float, float]] = None,
) -> bpy.types.Object:
    """Create a parametric female peg receiver socket cavity tool as a closed manifold mesh.

    Geometry Policy:
    Generates a closed, watertight 2-manifold cutter volume representing the negative
    receiver cavity for a cylindrical peg connector. The cavity extends along local +Z
    from the opening plane at z = 0 to the flat closed bottom at z = +socket_depth_mm.
    The opening plane at z = 0 is sealed with a planar circular cap to ensure the cutter
    is a closed 2-manifold solid.

    Clearance Contract:
    Radial clearance is applied uniformly:
        socket_diameter = peg_diameter + 2 * radial_clearance

    Orientation & Coordinates:
    - Default location: 3D Cursor position (or specified location).
    - Local origin: (0, 0, 0) at the center of the planar opening face (z = 0).
    - Socket cavity axis (kf_axis): (0.0, 0.0, 1.0) pointing along the cavity depth.
    - Insertion direction (kf_insertion_axis): (0.0, 0.0, 1.0) (male peg travel into cavity).
    - Opening outward normal (kf_opening_normal): (0.0, 0.0, -1.0) (pointing outward from opening plane).
    - Cavity depth: extends from z = 0 to z = +socket_depth_mm.

    Transactional Safety:
    On ANY failure after scene mutation begins, all allocated resources are
    deterministically cleaned up before raising KineFigGeometryError.

    Returns:
        The created KineFig socket object (e.g. KF_Socket_Peg_001).
    """
    validate_peg_socket_parameters(
        peg_diameter_mm=peg_diameter_mm,
        radial_clearance_mm=radial_clearance_mm,
        socket_depth_mm=socket_depth_mm,
        segments=segments,
    )

    if context is None:
        raise KineFigGeometryError("Blender context is required to create peg socket geometry")

    scale_length = get_scene_scale_length(context)
    socket_diameter_mm = compute_socket_diameter(peg_diameter_mm, radial_clearance_mm)
    socket_diameter_m = mm_to_blender(socket_diameter_mm, scale_length)
    socket_radius_m = socket_diameter_m / 2.0
    socket_depth_m = mm_to_blender(socket_depth_mm, scale_length)

    collection = (
        context.collection
        if hasattr(context, "collection") and context.collection
        else (context.scene.collection if hasattr(context, "scene") else None)
    )

    existing_names = [o.name for o in bpy.data.objects] if hasattr(bpy.data, "objects") else []
    object_name = get_next_object_name("Socket", detail="Peg", existing_names=existing_names)
    mesh_name = f"{object_name}_Mesh"

    created_objects = []
    created_meshes = []

    try:
        socket_mesh = bpy.data.meshes.new(mesh_name)
        created_meshes.append(socket_mesh)

        bm = bmesh.new()
        try:
            bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                segments=int(segments),
                radius1=socket_radius_m,
                radius2=socket_radius_m,
                depth=socket_depth_m,
            )
            bmesh.ops.translate(
                bm,
                vec=(0.0, 0.0, socket_depth_m / 2.0),
                verts=bm.verts,
            )
            bm.to_mesh(socket_mesh)
        finally:
            bm.free()

        socket_obj = bpy.data.objects.new(object_name, socket_mesh)
        created_objects.append(socket_obj)

        if collection and hasattr(collection, "objects"):
            collection.objects.link(socket_obj)

        # Set location
        if location is not None:
            socket_obj.location = location
        elif hasattr(context, "scene") and hasattr(context.scene, "cursor"):
            socket_obj.location = context.scene.cursor.location

        # Set factual KineFig metadata only
        socket_obj["kf_type"] = "socket"
        socket_obj["kf_socket_type"] = "peg"
        socket_obj["kf_version"] = VERSION
        socket_obj["kf_peg_diameter_mm"] = round(float(peg_diameter_mm), 4)
        socket_obj["kf_radial_clearance_mm"] = round(float(radial_clearance_mm), 4)
        socket_obj["kf_socket_diameter_mm"] = round(float(socket_diameter_mm), 4)
        socket_obj["kf_socket_depth_mm"] = round(float(socket_depth_mm), 4)
        socket_obj["kf_axis"] = (0.0, 0.0, 1.0)
        socket_obj["kf_insertion_axis"] = (0.0, 0.0, 1.0)
        socket_obj["kf_opening_normal"] = (0.0, 0.0, -1.0)

        log_info(
            f"Created Peg socket: {socket_obj.name}",
            name=socket_obj.name,
            peg_diameter_mm=peg_diameter_mm,
            radial_clearance_mm=radial_clearance_mm,
            socket_diameter_mm=socket_diameter_mm,
            socket_depth_mm=socket_depth_mm,
        )

        return socket_obj

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

        log_error(f"create_peg_socket_geometry failed and rolled back cleanly: {exc}")

        if isinstance(exc, KineFigError):
            raise
        raise KineFigGeometryError(f"Failed to create peg socket geometry: {exc}") from exc

