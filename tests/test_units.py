"""Unit tests for core/units.py."""

import pytest
from addon.kinefig.core.units import MM_TO_M, mm_to_blender, blender_to_mm


def test_mm_to_m_constant():
    """Verify that MM_TO_M is exactly 0.001 (1 Blender Unit = 1 meter)."""
    assert MM_TO_M == 0.001


@pytest.mark.parametrize(
    "mm_val, expected_m",
    [
        (0.0, 0.0),
        (1.0, 0.001),
        (5.0, 0.005),
        (10.0, 0.010),
        (100.0, 0.100),
        (1000.0, 1.0),
        (-10.0, -0.010),
    ],
)
def test_mm_to_blender_conversion(mm_val, expected_m):
    """Verify mm_to_blender converts millimeters to Blender internal meters correctly."""
    result = mm_to_blender(mm_val)
    assert pytest.approx(result) == expected_m
    assert isinstance(result, float)


@pytest.mark.parametrize(
    "m_val, expected_mm",
    [
        (0.0, 0.0),
        (0.001, 1.0),
        (0.005, 5.0),
        (0.010, 10.0),
        (0.100, 100.0),
        (1.0, 1000.0),
        (-0.010, -10.0),
    ],
)
def test_blender_to_mm_conversion(m_val, expected_mm):
    """Verify blender_to_mm converts Blender internal meters to millimeters correctly."""
    result = blender_to_mm(m_val)
    assert pytest.approx(result) == expected_mm
    assert isinstance(result, float)


@pytest.mark.parametrize("val", [0.0, 0.125, 2.5, 12.7, 50.0, 250.0])
def test_units_round_trip(val):
    """Verify round trip conversion (mm -> m -> mm) retains accuracy."""
    m = mm_to_blender(val)
    back_to_mm = blender_to_mm(m)
    assert pytest.approx(back_to_mm) == val


def test_units_independent_of_display():
    """Verify that unit math is pure and invariant (does not depend on scene display units)."""
    # 10 mm ball joint must strictly be 0.010 meters in Blender coordinates
    diameter_mm = 10.0
    radius_bu = mm_to_blender(diameter_mm / 2.0)
    assert pytest.approx(radius_bu) == 0.005
    assert pytest.approx(radius_bu * 2.0) == 0.010


def test_units_invalid_type():
    """Verify conversion fails on non-numeric types."""
    with pytest.raises((ValueError, TypeError)):
        mm_to_blender("invalid")

    with pytest.raises((ValueError, TypeError)):
        blender_to_mm("invalid")
