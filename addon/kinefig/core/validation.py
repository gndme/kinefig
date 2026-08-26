"""Validation primitives for KineFig parameters."""

import math
from typing import Union
from .errors import KineFigValidationError

Numeric = Union[int, float]


def require_positive(value: Numeric, name: str) -> float:
    """Validate that value is a finite number greater than zero."""
    val = float(value)
    if not math.isfinite(val):
        raise KineFigValidationError(f"{name} must be a finite number, got {value}")
    if val <= 0:
        raise KineFigValidationError(f"{name} must be greater than 0, got {value}")
    return val


def require_non_negative(value: Numeric, name: str) -> float:
    """Validate that value is a finite number greater than or equal to zero."""
    val = float(value)
    if not math.isfinite(val):
        raise KineFigValidationError(f"{name} must be a finite number, got {value}")
    if val < 0:
        raise KineFigValidationError(f"{name} must be 0 or greater, got {value}")
    return val


def require_in_range(
    value: Numeric, min_val: Numeric, max_val: Numeric, name: str
) -> float:
    """Validate that value is within [min_val, max_val] inclusive with finite bounds."""
    val = float(value)
    min_f = float(min_val)
    max_f = float(max_val)

    if not math.isfinite(val):
        raise KineFigValidationError(f"{name} must be a finite number, got {value}")
    if not math.isfinite(min_f) or not math.isfinite(max_f):
        raise ValueError(f"Range bounds must be finite numbers, got min={min_val}, max={max_val}")
    if min_f > max_f:
        raise ValueError(f"Invalid range: min ({min_f}) cannot be greater than max ({max_f})")
    if not (min_f <= val <= max_f):
        raise KineFigValidationError(
            f"{name} must be between {min_f} and {max_f}, got {value}"
        )
    return val


def validate_ball_joint_parameters(
    ball_diameter_mm: Numeric,
    stem_diameter_mm: Numeric,
    stem_length_mm: Numeric,
    segments: int = 32,
    rings: int = 16,
) -> None:
    """Validate parametric inputs for a male ball joint.

    Enforces:
    - ball_diameter_mm > 0 and finite
    - stem_diameter_mm > 0 and finite
    - stem_length_mm > 0 and finite
    - stem_diameter_mm < ball_diameter_mm (stem must fit inside the ball)
    - segments and rings in valid integer bounds [3, 256]
    """
    ball_d = require_positive(ball_diameter_mm, "ball_diameter_mm")
    stem_d = require_positive(stem_diameter_mm, "stem_diameter_mm")
    require_positive(stem_length_mm, "stem_length_mm")

    if stem_d >= ball_d:
        raise KineFigValidationError(
            f"Stem diameter ({stem_d} mm) must be less than ball diameter ({ball_d} mm)"
        )

    require_in_range(segments, 3, 256, "segments")
    require_in_range(rings, 3, 256, "rings")
