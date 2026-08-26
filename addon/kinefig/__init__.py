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
from .ui.panel import KINEFIG_PT_main

_CLASSES = (
    KINEFIG_OT_create_smoke_object,
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
