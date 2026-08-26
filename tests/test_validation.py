"""Unit tests for core/validation.py."""

import math
import pytest
from addon.kinefig.core.validation import (
    require_positive,
    require_non_negative,
    require_in_range,
    require_integer_in_range,
    validate_ball_joint_parameters,
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
    """Verify require_non_negative raises KineFigValidationError for < 0."""
    with pytest.raises(KineFigValidationError, match="must be 0 or greater"):
        require_non_negative(invalid_val, "offset")


@pytest.mark.parametrize("non_finite_val", [float("nan"), float("inf"), float("-inf")])
def test_require_non_negative_non_finite(non_finite_val):
    """Verify require_non_negative rejects non-finite numbers with KineFigValidationError."""
    with pytest.raises(KineFigValidationError, match="must be a finite number"):
        require_non_negative(non_finite_val, "offset")


def test_require_in_range_success():
    """Verify require_in_range accepts numbers within [min_val, max_val] inclusive."""
    assert require_in_range(0.0, 0.0, 1.0, "factor") == 0.0
    assert require_in_range(0.5, 0.0, 1.0, "factor") == 0.5
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


# ==============================================================================
# Strict Integer In Range Tests (FINDING MEDIUM-01)
# ==============================================================================

def test_require_integer_in_range_success():
    """Verify require_integer_in_range accepts valid boundary and intermediate ints."""
    assert require_integer_in_range(3, 3, 256, "segments") == 3
    assert require_integer_in_range(256, 3, 256, "segments") == 256
    assert require_integer_in_range(32, 3, 256, "segments") == 32
    assert require_integer_in_range(16, 3, 256, "rings") == 16


@pytest.mark.parametrize(
    "invalid_input",
    [
        2,              # 2 FAIL (below min)
        257,            # 257 FAIL (above max)
        3.5,            # 3.5 FAIL (fractional float)
        31.7,           # 31.7 FAIL (fractional float)
        32.0,           # 32.0 FAIL (whole float - strict policy: reject float entirely)
        True,           # True FAIL (bool rejected despite being int subclass)
        False,          # False FAIL (bool rejected)
        float("nan"),   # NaN FAIL
        float("inf"),   # +inf FAIL
        float("-inf"),  # -inf FAIL
        "32",           # "32" FAIL (string rejected)
        None,           # None FAIL
        [32],           # list FAIL
    ],
)
def test_require_integer_in_range_failures(invalid_input):
    """Verify require_integer_in_range rejects out-of-range ints, floats, bools, strings."""
    with pytest.raises(KineFigValidationError):
        require_integer_in_range(invalid_input, 3, 256, "segments")


def test_require_integer_in_range_invalid_bounds():
    """Verify require_integer_in_range raises ValueError for invalid bounds."""
    with pytest.raises(ValueError, match="Invalid range"):
        require_integer_in_range(10, 100, 5, "segments")
    with pytest.raises(ValueError, match="Range bounds must be integers"):
        require_integer_in_range(10, 3.0, 256, "segments")  # type: ignore
    with pytest.raises(ValueError, match="Range bounds must be integers"):
        require_integer_in_range(10, True, 256, "segments")  # type: ignore


# ==============================================================================
# Ball Joint Parameter Validation Tests
# ==============================================================================

def test_validate_ball_joint_parameters_valid():
    """Verify validate_ball_joint_parameters accepts standard valid dimensions."""
    validate_ball_joint_parameters(
        ball_diameter_mm=5.0,
        stem_diameter_mm=3.0,
        stem_length_mm=5.0,
        segments=32,
        rings=16,
    )


@pytest.mark.parametrize(
    "bad_ball, bad_stem, bad_len",
    [
        (0.0, 3.0, 5.0),
        (-5.0, 3.0, 5.0),
        (5.0, 0.0, 5.0),
        (5.0, -3.0, 5.0),
        (5.0, 3.0, 0.0),
        (5.0, 3.0, -5.0),
        (float("nan"), 3.0, 5.0),
        (5.0, float("inf"), 5.0),
        (5.0, 3.0, float("-inf")),
    ],
)
def test_validate_ball_joint_parameters_non_positive_or_non_finite(bad_ball, bad_stem, bad_len):
    """Verify validate_ball_joint_parameters rejects <= 0 or non-finite dimensions."""
    with pytest.raises(KineFigValidationError):
        validate_ball_joint_parameters(bad_ball, bad_stem, bad_len)


def test_validate_ball_joint_parameters_stem_ge_ball():
    """Verify validate_ball_joint_parameters rejects stem diameter >= ball diameter."""
    with pytest.raises(KineFigValidationError, match="must be less than ball diameter"):
        validate_ball_joint_parameters(5.0, 5.0, 5.0)

    with pytest.raises(KineFigValidationError, match="must be less than ball diameter"):
        validate_ball_joint_parameters(5.0, 6.0, 5.0)


@pytest.mark.parametrize(
    "bad_seg, bad_ring",
    [
        (2, 16),
        (32, 2),
        (0, 16),
        (32, -1),
        (500, 16),
        (31.7, 16),
        (32, 15.9),
        (32.0, 16),
        (True, 16),
        ("32", 16),
    ],
)
def test_validate_ball_joint_parameters_invalid_tessellation(bad_seg, bad_ring):
    """Verify validate_ball_joint_parameters rejects out-of-range, non-int segments/rings."""
    with pytest.raises(KineFigValidationError):
        validate_ball_joint_parameters(5.0, 3.0, 5.0, segments=bad_seg, rings=bad_ring)
