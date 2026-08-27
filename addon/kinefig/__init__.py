bl_info = {
    "name": "KineFig",
    "author": "gndme",
    "version": (0, 0, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > KineFig",
    "description": "Articulated action-figure tools",
    "category": "3D View",
}

import bpy

from .properties.joint_properties import (
    KineFigBallJointProperties,
    KineFigDoubleBallJointProperties,
    KineFigPegJointProperties,
)
from .properties.socket_properties import (
    KineFigBallSocketProperties,
    KineFigPegSocketProperties,
)
from .operators.smoke import KINEFIG_OT_create_smoke_object
from .operators.joints import (
    KINEFIG_OT_create_ball_joint,
    KINEFIG_OT_create_double_ball_joint,
    KINEFIG_OT_create_peg_joint,
)
from .operators.sockets import (
    KINEFIG_OT_create_ball_socket,
    KINEFIG_OT_use_selected_ball,
    KINEFIG_OT_create_peg_socket,
    KINEFIG_OT_use_selected_peg,
)
from .operators.diagnostics import (
    KINEFIG_OT_copy_debug_info,
    KINEFIG_OT_export_diagnostic_report,
    KINEFIG_OT_report_bug,
)
from .ui.panel import KINEFIG_PT_main

_CLASSES = (
    KineFigBallJointProperties,
    KineFigDoubleBallJointProperties,
    KineFigPegJointProperties,
    KineFigBallSocketProperties,
    KineFigPegSocketProperties,
    KINEFIG_OT_create_smoke_object,
    KINEFIG_OT_create_ball_joint,
    KINEFIG_OT_create_double_ball_joint,
    KINEFIG_OT_create_peg_joint,
    KINEFIG_OT_create_ball_socket,
    KINEFIG_OT_use_selected_ball,
    KINEFIG_OT_create_peg_socket,
    KINEFIG_OT_use_selected_peg,
    KINEFIG_OT_copy_debug_info,
    KINEFIG_OT_export_diagnostic_report,
    KINEFIG_OT_report_bug,
    KINEFIG_PT_main,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.kinefig_ball_joint = bpy.props.PointerProperty(
        type=KineFigBallJointProperties
    )
    bpy.types.Scene.kinefig_double_ball_joint = bpy.props.PointerProperty(
        type=KineFigDoubleBallJointProperties
    )
    bpy.types.Scene.kinefig_ball_socket = bpy.props.PointerProperty(
        type=KineFigBallSocketProperties
    )
    bpy.types.Scene.kinefig_peg_joint = bpy.props.PointerProperty(
        type=KineFigPegJointProperties
    )
    bpy.types.Scene.kinefig_peg_socket = bpy.props.PointerProperty(
        type=KineFigPegSocketProperties
    )


def unregister():
    if hasattr(bpy.types.Scene, "kinefig_peg_socket"):
        del bpy.types.Scene.kinefig_peg_socket
    if hasattr(bpy.types.Scene, "kinefig_peg_joint"):
        del bpy.types.Scene.kinefig_peg_joint
    if hasattr(bpy.types.Scene, "kinefig_double_ball_joint"):
        del bpy.types.Scene.kinefig_double_ball_joint
    if hasattr(bpy.types.Scene, "kinefig_ball_socket"):
        del bpy.types.Scene.kinefig_ball_socket
    if hasattr(bpy.types.Scene, "kinefig_ball_joint"):
        del bpy.types.Scene.kinefig_ball_joint
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
