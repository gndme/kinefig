"""Main 3D Viewport sidebar panel for KineFig."""

import bpy
from ..core.build_info import VERSION, get_short_sha
from ..core.clearance import compute_socket_diameter


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
        active_obj = getattr(context, "active_object", None)

        # 1. Version and Build Badge (Required for UAT bug traceability)
        header_box = layout.box()
        header_box.label(text=f"KineFig v{VERSION}", icon="MESH_UVSPHERE")
        sub_row = header_box.row()
        sub_row.scale_y = 0.8
        sub_row.label(text=f"Build: {get_short_sha()}", icon="FILE_TEXT")

        # 2. JOINT Category
        # 2A. Male Ball Joint (PR-002)
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
            joint_box.operator(
                "kinefig.create_ball_joint",
                text="Create Ball Joint",
                icon="ADD",
            )

        # 2B. Female Ball Socket Cavity (PR-003)
        socket_box = layout.box()
        socket_box.label(text="JOINT: Ball Socket Cavity", icon="MOD_MESHDEFORM")

        # Contextual UX link: if active object is a KineFig Ball Joint, offer button to copy diameter
        if (
            active_obj
            and active_obj.get("kf_type") == "joint"
            and active_obj.get("kf_joint_type") == "ball"
            and "kf_ball_diameter_mm" in active_obj
        ):
            link_row = socket_box.row()
            link_row.operator(
                "kinefig.use_selected_ball",
                text=f"Match Selected Ball ({active_obj.get('kf_ball_diameter_mm'):.1f}mm)",
                icon="EYEDROPPER",
            )

        if hasattr(scene, "kinefig_ball_socket"):
            sprops = scene.kinefig_ball_socket
            scol = socket_box.column(align=True)
            scol.prop(sprops, "ball_diameter_mm", text="Ball Diameter")
            scol.prop(sprops, "clearance_mm", text="Clearance")
            scol.prop(sprops, "socket_depth_mm", text="Socket Depth")

            # Computed nominal socket cavity diameter readout
            computed_d = compute_socket_diameter(sprops.ball_diameter_mm, sprops.clearance_mm)
            readout = socket_box.row()
            readout.scale_y = 0.8
            readout.label(text=f"Cavity Dia: {computed_d:.2f} mm (radial clr: {sprops.clearance_mm:.2f}mm)", icon="INFO")

            sop = socket_box.operator(
                "kinefig.create_ball_socket",
                text="Create Ball Socket",
                icon="ADD",
            )
            sop.ball_diameter_mm = sprops.ball_diameter_mm
            sop.clearance_mm = sprops.clearance_mm
            sop.socket_depth_mm = sprops.socket_depth_mm
            sop.segments = sprops.segments
            sop.rings = sprops.rings
        else:
            socket_box.operator(
                "kinefig.create_ball_socket",
                text="Create Ball Socket",
                icon="ADD",
            )

        # 2C. Male Peg Joint (PR-005)
        peg_box = layout.box()
        peg_box.label(text="JOINT: Male Peg Joint", icon="MESH_CYLINDER")

        if hasattr(scene, "kinefig_peg_joint"):
            peg_props = scene.kinefig_peg_joint
            peg_col = peg_box.column(align=True)
            peg_col.prop(peg_props, "peg_diameter_mm", text="Peg Dia")
            peg_col.prop(peg_props, "peg_length_mm", text="Peg Length")
            peg_col.prop(peg_props, "taper_angle_deg", text="Taper Angle")

            pop = peg_box.operator(
                "kinefig.create_peg_joint",
                text="Create Peg Joint",
                icon="ADD",
            )
            pop.peg_diameter_mm = peg_props.peg_diameter_mm
            pop.peg_length_mm = peg_props.peg_length_mm
            pop.taper_angle_deg = peg_props.taper_angle_deg
            pop.segments = peg_props.segments
        else:
            peg_box.operator(
                "kinefig.create_peg_joint",
                text="Create Peg Joint",
                icon="ADD",
            )

        # 2D. Female Peg Socket Receiver (PR-005)
        psocket_box = layout.box()
        psocket_box.label(text="JOINT: Peg Socket Receiver", icon="SNAP_FACE")

        # Contextual UX link: if active object is a KineFig Peg Joint, offer button to copy diameter
        if (
            active_obj
            and active_obj.get("kf_type") == "joint"
            and active_obj.get("kf_joint_type") == "peg"
            and "kf_peg_diameter_mm" in active_obj
        ):
            link_row = psocket_box.row()
            link_row.operator(
                "kinefig.use_selected_peg",
                text=f"Match Selected Peg ({active_obj.get('kf_peg_diameter_mm'):.1f}mm)",
                icon="EYEDROPPER",
            )

        if hasattr(scene, "kinefig_peg_socket"):
            psprops = scene.kinefig_peg_socket
            pscol = psocket_box.column(align=True)
            pscol.prop(psprops, "peg_diameter_mm", text="Peg Dia")
            pscol.prop(psprops, "radial_clearance_mm", text="Clearance")
            pscol.prop(psprops, "socket_depth_mm", text="Socket Depth")

            # Computed nominal socket cavity diameter readout
            computed_peg_d = compute_socket_diameter(psprops.peg_diameter_mm, psprops.radial_clearance_mm)
            preadout = psocket_box.row()
            preadout.scale_y = 0.8
            preadout.label(
                text=f"Cavity Dia: {computed_peg_d:.2f} mm (radial clr: {psprops.radial_clearance_mm:.2f}mm)",
                icon="INFO",
            )

            psop = psocket_box.operator(
                "kinefig.create_peg_socket",
                text="Create Peg Socket",
                icon="ADD",
            )
            psop.peg_diameter_mm = psprops.peg_diameter_mm
            psop.radial_clearance_mm = psprops.radial_clearance_mm
            psop.socket_depth_mm = psprops.socket_depth_mm
            psop.segments = psprops.segments
        else:
            psocket_box.operator(
                "kinefig.create_peg_socket",
                text="Create Peg Socket",
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
