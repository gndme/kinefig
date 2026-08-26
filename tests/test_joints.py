"""Unit tests for joint geometry core functions."""

from unittest.mock import MagicMock
import pytest
import bpy
from addon.kinefig.core.units import mm_to_blender
from addon.kinefig.core.validation import validate_ball_joint_parameters
from addon.kinefig.core.naming import get_next_object_name, is_temp_object
from addon.kinefig.core.errors import KineFigValidationError, KineFigGeometryError
from addon.kinefig.geometry.joints import create_ball_joint_geometry


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


def test_ball_joint_factual_metadata_and_absence_of_unknowns():
    """Verify FINDING MEDIUM-03: uncomputed metadata keys are absent from joint object."""
    context = MagicMock()
    context.collection = MagicMock()
    context.scene.cursor.location = (0.0, 0.0, 0.0)

    eval_mesh_mock = MagicMock()
    eval_mesh_mock.vertices = [1, 2, 3]
    bpy.data.meshes.new_from_object = MagicMock(return_value=eval_mesh_mock)

    obj = create_ball_joint_geometry(
        context=context,
        ball_diameter_mm=5.0,
        stem_diameter_mm=3.0,
        stem_length_mm=5.0,
    )

    # Factual metadata must exist
    assert obj.get("kf_type") == "joint"
    assert obj.get("kf_joint_type") == "ball"
    assert obj.get("kf_ball_diameter_mm") == 5.0
    assert obj.get("kf_stem_diameter_mm") == 3.0
    assert obj.get("kf_stem_length_mm") == 5.0
    assert obj.get("kf_axis") == (0.0, 0.0, 1.0)

    # Unknown / uncomputed metadata must NOT exist
    assert "kf_range_min" not in obj
    assert "kf_range_max" not in obj
    assert "kf_clearance_mm" not in obj
    assert "kf_role" not in obj
    assert "kf_side" not in obj


def test_ball_joint_transactional_rollback_on_boolean_failure():
    """Verify FINDING HIGH-01: Boolean failure triggers full rollback of all allocated resources."""
    # Pre-existing unrelated scene object that must survive untouched
    unrelated = bpy.data.objects.new("User_Mesh")

    context = MagicMock()
    context.collection = MagicMock()
    context.scene.cursor.location = (0.0, 0.0, 0.0)

    # Trigger failure via controlled test hook
    with pytest.raises(KineFigGeometryError, match="Injected Boolean failure"):
        create_ball_joint_geometry(
            context=context,
            ball_diameter_mm=5.0,
            stem_diameter_mm=3.0,
            stem_length_mm=5.0,
            _inject_boolean_failure=True,
        )

    # Assert that no partial joint or temp objects remain
    remaining_names = [o.name for o in bpy.data.objects]
    assert remaining_names == ["User_Mesh"], f"Orphan objects found: {remaining_names}"

    # Assert no temp mesh datablocks remain
    temp_meshes = [m.name for m in bpy.data.meshes if is_temp_object(m.name)]
    assert len(temp_meshes) == 0, f"Orphan temp meshes found: {temp_meshes}"
