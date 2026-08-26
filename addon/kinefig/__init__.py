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

from .operators.smoke import KINEFIG_OT_create_smoke_object
from .operators.diagnostics import (
    KINEFIG_OT_copy_debug_info,
    KINEFIG_OT_export_diagnostic_report,
    KINEFIG_OT_report_bug,
)
from .ui.panel import KINEFIG_PT_main

_CLASSES = (
    KINEFIG_OT_create_smoke_object,
    KINEFIG_OT_copy_debug_info,
    KINEFIG_OT_export_diagnostic_report,
    KINEFIG_OT_report_bug,
    KINEFIG_PT_main,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
