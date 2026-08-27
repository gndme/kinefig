"""Boolean evaluation helper for Blender geometry engine."""

from typing import Any
import bpy

from ..core.errors import KineFigGeometryError


def evaluate_boolean_modifier(
    context: Any,
    obj: bpy.types.Object,
    mod: bpy.types.Modifier,
    operation_name: str = "Boolean modifier",
) -> bpy.types.Mesh:
    """Evaluate a modifier via depsgraph and return the evaluated mesh.

    Provides a clean, reusable evaluation seam for Boolean operations
    across all joint and socket geometry engines.
    """
    if not hasattr(context, "evaluated_depsgraph_get"):
        raise KineFigGeometryError("Context has no evaluated_depsgraph_get method")

    depsgraph = context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    eval_mesh = bpy.data.meshes.new_from_object(eval_obj)

    if eval_mesh is None:
        raise KineFigGeometryError(f"{operation_name} failed to generate evaluated mesh")

    try:
        vert_count = len(eval_mesh.vertices)
    except (TypeError, AttributeError):
        raise KineFigGeometryError(
            f"Evaluated mesh from {operation_name} has invalid or missing vertices"
        )

    if vert_count == 0:
        raise KineFigGeometryError(
            f"{operation_name} produced empty mesh geometry (0 vertices)"
        )

    return eval_mesh
