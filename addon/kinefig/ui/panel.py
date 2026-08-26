"""Main 3D Viewport sidebar panel for KineFig."""

import bpy
from ..core.build_info import VERSION, get_short_sha


class KINEFIG_PT_main(bpy.types.Panel):
    """Main KineFig sidebar panel in 3D Viewport."""

    bl_label = "KineFig"
    bl_idname = "KINEFIG_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KineFig"

    def draw(self, context):
        layout = self.layout

        # 1. Version and Build Badge (Required for UAT bug traceability)
        header_box = layout.box()
        header_box.label(text=f"KineFig v{VERSION}", icon="MESH_UVSPHERE")
        sub_row = header_box.row()
        sub_row.scale_y = 0.8
        sub_row.label(text=f"Build: {get_short_sha()}", icon="FILE_TEXT")

        # 2. Smoke Geometry Test
        smoke_box = layout.box()
        smoke_box.label(text="Foundation Verification:", icon="EXPERIMENTAL")
        smoke_box.operator(
            "kinefig.create_smoke_object",
            text="Create Test Ball (10mm)",
            icon="SPHERE",
        )

        # 3. Help & Diagnostics (UAT Bug Reporting System)
        diag_box = layout.box()
        diag_box.label(text="Help & Diagnostics:", icon="HELP")
        row = diag_box.row(align=True)
        row.operator("kinefig.copy_debug_info", text="Copy Debug Info", icon="COPYDOWN")
        diag_box.operator("kinefig.export_diagnostic_report", text="Export Diagnostic Report", icon="PACKAGE")
        diag_box.operator("kinefig.report_bug", text="Report Bug on GitHub", icon="URL")
