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
