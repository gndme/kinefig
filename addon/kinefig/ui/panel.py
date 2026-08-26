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
        scene = context.scene

        # 1. Version and Build Badge (Required for UAT bug traceability)
        header_box = layout.box()
        header_box.label(text=f"KineFig v{VERSION}", icon="MESH_UVSPHERE")
        sub_row = header_box.row()
        sub_row.scale_y = 0.8
        sub_row.label(text=f"Build: {get_short_sha()}", icon="FILE_TEXT")

        # 2. JOINT Category — Parametric Ball Joint
        joint_box = layout.box()
        joint_box.label(text="JOINT: Male Ball Joint", icon="MESH_UVSPHERE")

        if hasattr(scene, "kinefig_ball_joint"):
            props = scene.kinefig_ball_joint
            col = joint_box.column(align=True)
            col.prop(props, "ball_diameter_mm", text="Ball Diameter")
            col.prop(props, "stem_diameter_mm", text="Stem Diameter")
            col.prop(props, "stem_length_mm", text="Stem Length")

            op = joint_box.operator(
                "kinefig.create_ball_joint",
                text="Create Ball Joint",
                icon="ADD",
            )
            op.ball_diameter_mm = props.ball_diameter_mm
            op.stem_diameter_mm = props.stem_diameter_mm
            op.stem_length_mm = props.stem_length_mm
            op.segments = props.segments
            op.rings = props.rings
        else:
            # Fallback if properties not yet registered on scene
            joint_box.operator(
                "kinefig.create_ball_joint",
                text="Create Ball Joint",
                icon="ADD",
            )

        # 3. Help & Diagnostics (UAT Bug Reporting System)
        diag_box = layout.box()
        diag_box.label(text="Help & Diagnostics:", icon="HELP")
        row = diag_box.row(align=True)
        row.operator("kinefig.copy_debug_info", text="Copy Debug Info", icon="COPYDOWN")
        diag_box.operator("kinefig.export_diagnostic_report", text="Export Diagnostic Report", icon="PACKAGE")
        diag_box.operator("kinefig.report_bug", text="Report Bug on GitHub", icon="URL")

        # Verification helper
        sub_box = diag_box.box()
        sub_box.label(text="Verification Smoke:", icon="EXPERIMENTAL")
        sub_box.operator(
            "kinefig.create_smoke_object",
            text="Test Ball (10mm)",
            icon="SPHERE",
        )
