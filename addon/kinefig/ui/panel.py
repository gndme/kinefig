"""Main 3D Viewport sidebar panel for KineFig."""

import bpy


class KINEFIG_PT_main(bpy.types.Panel):
    """Main KineFig sidebar panel in 3D Viewport."""

    bl_label = "KineFig"
    bl_idname = "KINEFIG_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KineFig"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Foundation Smoke Test")
        layout.operator("kinefig.create_smoke_object", text="Create Test Ball (10mm)", icon="SPHERE")
