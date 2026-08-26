"""Validation primitives for KineFig parameters."""

import math
from typing import Any, Union
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


def require_integer_in_range(
    value: Any, min_val: int, max_val: int, name: str
) -> int:
    """Validate that value is strictly an int within [min_val, max_val] inclusive.

    Policy:
    - Strictly requires actual int type (rejects float, bool, str, None, NaN, inf).
    - Float with fractional part (e.g. 31.7, 3.5) is rejected with KineFigValidationError.
    - Float with whole number value (e.g. 32.0) is also rejected (no silent coercion).
    - Booleans (True/False) are explicitly rejected despite being a subclass of int in Python.
    """
    if isinstance(value, bool):
        raise KineFigValidationError(f"{name} must be an integer, got bool ({value})")

    if not isinstance(value, int):
        raise KineFigValidationError(
            f"{name} must be an integer, got {type(value).__name__} ({value})"
        )

    if (
        not isinstance(min_val, int)
        or isinstance(min_val, bool)
        or not isinstance(max_val, int)
        or isinstance(max_val, bool)
    ):
        raise ValueError(f"Range bounds must be integers, got min={min_val}, max={max_val}")

    if min_val > max_val:
        raise ValueError(f"Invalid range: min ({min_val}) cannot be greater than max ({max_val})")

    if not (min_val <= value <= max_val):
        raise KineFigValidationError(
            f"{name} must be an integer between {min_val} and {max_val}, got {value}"
        )

    return value


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
    - segments and rings strictly in valid integer bounds [3, 256]
    """
    ball_d = require_positive(ball_diameter_mm, "ball_diameter_mm")
    stem_d = require_positive(stem_diameter_mm, "stem_diameter_mm")
    require_positive(stem_length_mm, "stem_length_mm")

    if stem_d >= ball_d:
        raise KineFigValidationError(
            f"Stem diameter ({stem_d} mm) must be less than ball diameter ({ball_d} mm)"
        )

    require_integer_in_range(segments, 3, 256, "segments")
    require_integer_in_range(rings, 3, 256, "rings")


def validate_ball_socket_parameters(
    ball_diameter_mm: Numeric,
    clearance_mm: Numeric,
    socket_depth_mm: Numeric,
    segments: int = 32,
    rings: int = 16,
) -> None:
    """Validate parametric inputs for a female ball socket cavity.

    Enforces:
    - ball_diameter_mm > 0 and finite
    - clearance_mm >= 0 and finite (radial clearance)
    - socket_depth_mm > 0 and finite
    - socket_depth_mm < socket_diameter_mm (depth cannot exceed cavity diameter)
    - segments and rings strictly in valid integer bounds [3, 256]
    """
    ball_d = require_positive(ball_diameter_mm, "ball_diameter_mm")
    clr = require_non_negative(clearance_mm, "clearance_mm")
    depth = require_positive(socket_depth_mm, "socket_depth_mm")

    socket_d = ball_d + 2.0 * clr
    if depth >= socket_d:
        raise KineFigValidationError(
            f"Socket depth ({depth:.2f} mm) must be less than internal socket diameter ({socket_d:.2f} mm)"
        )

    require_integer_in_range(segments, 3, 256, "segments")
    require_integer_in_range(rings, 3, 256, "rings")

