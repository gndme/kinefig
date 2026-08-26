"""Smoke test operator for KineFig foundation verification."""

import bpy
from ..core.units import mm_to_blender
from ..core.naming import get_next_object_name
from ..core.logging import log_info


class KINEFIG_OT_create_smoke_object(bpy.types.Operator):
    """Create a temporary KineFig test object (10mm UV sphere)"""

    bl_idname = "kinefig.create_smoke_object"
    bl_label = "Create Test Joint"
    bl_description = "Create a 10mm test ball joint to verify add-on operation and Undo"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" if hasattr(context, "mode") else True

    def execute(self, context):
        radius_m = mm_to_blender(5.0)  # 5mm radius = 10mm diameter
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius_m)
        obj = context.active_object
        if obj:
            # Allocate name deterministically without relying on Blender's fallback suffixes
            existing_names = [o.name for o in bpy.data.objects if o != obj]
            obj.name = get_next_object_name("Smoke", detail="Ball", existing_names=existing_names)
            obj["kf_type"] = "smoke"
            self.report({"INFO"}, f"Created test object: {obj.name}")
            log_info(f"Created smoke test object: {obj.name}", object_name=obj.name, diameter_mm=10.0)
        return {"FINISHED"}
