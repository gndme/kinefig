"""Unit tests for core/validation.py."""

import math
import pytest
from addon.kinefig.core.validation import (
    require_positive,
    require_non_negative,
    require_in_range,
)
from addon.kinefig.core.errors import KineFigValidationError


def test_require_positive_success():
    """Verify require_positive accepts positive finite numbers."""
    assert require_positive(1, "ball_diameter") == 1.0
    assert require_positive(0.001, "clearance") == 0.001
    assert require_positive(100.5, "length") == 100.5


@pytest.mark.parametrize("invalid_val", [0, 0.0, -1, -0.0001, -50.0])
def test_require_positive_failure(invalid_val):
    """Verify require_positive raises KineFigValidationError for <= 0."""
    with pytest.raises(KineFigValidationError, match="must be greater than 0"):
        require_positive(invalid_val, "ball_diameter")


@pytest.mark.parametrize("non_finite_val", [float("nan"), float("inf"), float("-inf")])
def test_require_positive_non_finite(non_finite_val):
    """Verify require_positive rejects NaN, +inf, -inf with KineFigValidationError."""
    with pytest.raises(KineFigValidationError, match="must be a finite number"):
        require_positive(non_finite_val, "ball_diameter")


def test_require_non_negative_success():
    """Verify require_non_negative accepts zero and positive finite numbers."""
    assert require_non_negative(0, "offset") == 0.0
    assert require_non_negative(0.0, "offset") == 0.0
    assert require_non_negative(5.5, "offset") == 5.5


@pytest.mark.parametrize("invalid_val", [-0.0001, -1, -10.0])
def test_require_non_negative_failure(invalid_val):
    """Verify require_non_negative raises KineFigValidationError for negative numbers."""
    with pytest.raises(KineFigValidationError, match="must be 0 or greater"):
        require_non_negative(invalid_val, "clearance")


@pytest.mark.parametrize("non_finite_val", [float("nan"), float("inf"), float("-inf")])
def test_require_non_negative_non_finite(non_finite_val):
    """Verify require_non_negative rejects NaN, +inf, -inf with KineFigValidationError."""
    with pytest.raises(KineFigValidationError, match="must be a finite number"):
        require_non_negative(non_finite_val, "clearance")


def test_require_in_range_success():
    """Verify require_in_range accepts values within [min, max]."""
    assert require_in_range(0.5, 0.0, 1.0, "factor") == 0.5
    assert require_in_range(0.0, 0.0, 1.0, "factor") == 0.0
    assert require_in_range(1.0, 0.0, 1.0, "factor") == 1.0


@pytest.mark.parametrize("out_of_range", [-0.1, 1.1, 10.0, -50.0])
def test_require_in_range_failure(out_of_range):
    """Verify require_in_range raises KineFigValidationError for values out of range."""
    with pytest.raises(KineFigValidationError, match="must be between"):
        require_in_range(out_of_range, 0.0, 1.0, "factor")


@pytest.mark.parametrize("non_finite_val", [float("nan"), float("inf"), float("-inf")])
def test_require_in_range_non_finite_value(non_finite_val):
    """Verify require_in_range rejects non-finite value with KineFigValidationError."""
    with pytest.raises(KineFigValidationError, match="must be a finite number"):
        require_in_range(non_finite_val, 0.0, 1.0, "factor")


@pytest.mark.parametrize("bad_min, bad_max", [(float("nan"), 1.0), (0.0, float("inf")), (float("-inf"), 1.0)])
def test_require_in_range_non_finite_bounds(bad_min, bad_max):
    """Verify require_in_range raises ValueError if range bounds are non-finite."""
    with pytest.raises(ValueError, match="Range bounds must be finite numbers"):
        require_in_range(0.5, bad_min, bad_max, "factor")


def test_require_in_range_inverted_bounds():
    """Verify require_in_range raises ValueError if min > max."""
    with pytest.raises(ValueError, match="Invalid range"):
        require_in_range(5.0, 10.0, 2.0, "factor")
