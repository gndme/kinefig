"""Unit conversion utilities.

All user-facing dimensions in KineFig are expressed in millimeters (mm).
Blender's internal unit length is meters (m) scaled by scene.unit_settings.scale_length.
"""

import math
from typing import Any, Union

MM_TO_M = 0.001
Numeric = Union[int, float]


def get_scene_scale_length(context: Any) -> float:
    """Safely extract unit scale_length from context or scene, defaulting to 1.0."""
    try:
        scene = getattr(context, "scene", context)
        unit_settings = getattr(scene, "unit_settings", None)
        if unit_settings and hasattr(unit_settings, "scale_length"):
            scale = float(unit_settings.scale_length)
            if scale > 0 and math.isfinite(scale):
                return scale
    except Exception:
        pass
    return 1.0


def mm_to_blender(value_mm: Numeric, scale_length: Numeric = 1.0) -> float:
    """Convert millimeters (UI) to Blender internal units (BU), respecting scene unit scale.

    Formula:
        internal_bu = (value_mm * 0.001) / scale_length
    """
    scale = float(scale_length) if scale_length and float(scale_length) > 0 else 1.0
    return (float(value_mm) * MM_TO_M) / scale


def blender_to_mm(value_m: Numeric, scale_length: Numeric = 1.0) -> float:
    """Convert Blender internal units (BU) to millimeters (UI), respecting scene unit scale.

    Formula:
        value_mm = (value_bu * scale_length) / 0.001
    """
    scale = float(scale_length) if scale_length and float(scale_length) > 0 else 1.0
    return (float(value_m) * scale) / MM_TO_M
