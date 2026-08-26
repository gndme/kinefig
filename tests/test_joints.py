"""Unit tests for joint geometry core functions."""

import pytest
from addon.kinefig.core.units import mm_to_blender, blender_to_mm
from addon.kinefig.core.validation import validate_ball_joint_parameters
from addon.kinefig.core.naming import get_next_object_name
from addon.kinefig.core.errors import KineFigValidationError


def test_ball_joint_unit_conversion():
    """Verify millimeter to Blender meter conversions for joint dimensions."""
    # 5.0 mm ball = 0.005 m, radius = 0.0025 m
    assert mm_to_blender(5.0) == 0.005
    assert mm_to_blender(5.0) / 2.0 == 0.0025

    # 3.0 mm stem = 0.003 m, radius = 0.0015 m
    assert mm_to_blender(3.0) == 0.003
    assert mm_to_blender(3.0) / 2.0 == 0.0015

    # 5.0 mm length = 0.005 m
    assert mm_to_blender(5.0) == 0.005


def test_ball_joint_parameter_validation_success():
    """Verify valid ball joint parameters pass validation."""
    validate_ball_joint_parameters(
        ball_diameter_mm=5.0,
        stem_diameter_mm=3.0,
        stem_length_mm=5.0,
        segments=32,
        rings=16,
    )


def test_ball_joint_parameter_validation_rejections():
    """Verify invalid ball joint parameters are rejected with KineFigValidationError."""
    # Stem diameter equal to or greater than ball diameter
    with pytest.raises(KineFigValidationError, match="must be less than ball diameter"):
        validate_ball_joint_parameters(5.0, 5.0, 5.0)

    with pytest.raises(KineFigValidationError, match="must be less than ball diameter"):
        validate_ball_joint_parameters(5.0, 5.5, 5.0)

    # Zero or negative
    with pytest.raises(KineFigValidationError):
        validate_ball_joint_parameters(0.0, 3.0, 5.0)

    with pytest.raises(KineFigValidationError):
        validate_ball_joint_parameters(5.0, 0.0, 5.0)

    with pytest.raises(KineFigValidationError):
        validate_ball_joint_parameters(5.0, 3.0, 0.0)


def test_ball_joint_sequential_naming():
    """Verify ball joint object names allocate sequentially without collisions."""
    existing = []
    name1 = get_next_object_name("Joint", detail="Ball", existing_names=existing)
    assert name1 == "KF_Joint_Ball_001"

    existing.append(name1)
    name2 = get_next_object_name("Joint", detail="Ball", existing_names=existing)
    assert name2 == "KF_Joint_Ball_002"

    existing.append(name2)
    name3 = get_next_object_name("Joint", detail="Ball", existing_names=existing)
    assert name3 == "KF_Joint_Ball_003"
