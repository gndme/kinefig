"""Unit conversion utilities.

All user-facing dimensions in KineFig are expressed in millimeters (mm).
Blender's internal unit length is meters (m).
"""

from typing import Union

MM_TO_M = 0.001
Numeric = Union[int, float]


def mm_to_blender(value_mm: Numeric) -> float:
    """Convert millimeters (UI) to Blender internal units (meters)."""
    return float(value_mm) * MM_TO_M


def blender_to_mm(value_m: Numeric) -> float:
    """Convert Blender internal units (meters) to millimeters (UI)."""
    return float(value_m) / MM_TO_M
