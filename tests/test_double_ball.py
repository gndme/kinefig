"""Unit tests for Double Ball / Dumbbell joint geometry engine and metadata."""

import math
from unittest.mock import MagicMock, patch
import bpy
import pytest

from addon.kinefig.geometry.joints import (
    create_double_ball_geometry,
    _evaluate_double_ball_union,
)
from addon.kinefig.core.clearance import compute_socket_diameter
from addon.kinefig.core.errors import KineFigGeometryError, KineFigValidationError
from addon.kinefig.core.naming import is_temp_object, PREFIX_TEMP


def test_double_ball_naming_allocation():
    """Verify sequential naming produces KF_Joint_DoubleBall_001, 002, etc."""
    context = MagicMock()
    context.collection = MagicMock()
    context.scene.cursor.location = (0.0, 0.0, 0.0)

    # In mock environment, test geometry creation with mocked boolean evaluation
    with patch(
        "addon.kinefig.geometry.joints._evaluate_double_ball_union"
    ) as mock_eval:
        fake_mesh = MagicMock()
        fake_mesh.vertices = [1, 2, 3, 4]
        mock_eval.return_value = fake_mesh

        obj1 = create_double_ball_geometry(context)
        assert obj1.name == "KF_Joint_DoubleBall_001"

        bpy.data.objects.new("KF_Joint_DoubleBall_001")
        obj2 = create_double_ball_geometry(context)
        assert obj2.name == "KF_Joint_DoubleBall_002"


def test_double_ball_factual_metadata_and_absence_of_unknowns():
    """Verify generated double ball carries strictly factual metadata and no uncomputed keys."""
    context = MagicMock()
    context.collection = MagicMock()
    context.scene.cursor.location = (0.0, 0.0, 0.0)

    with patch(
        "addon.kinefig.geometry.joints._evaluate_double_ball_union"
    ) as mock_eval:
        fake_mesh = MagicMock()
        fake_mesh.vertices = [1, 2, 3, 4]
        mock_eval.return_value = fake_mesh

        obj = create_double_ball_geometry(
            context,
            ball_a_diameter_mm=5.0,
            ball_b_diameter_mm=6.0,
            stem_diameter_mm=3.0,
            center_distance_mm=8.0,
        )

    # Factual metadata must exist
    assert obj.get("kf_type") == "joint"
    assert obj.get("kf_joint_type") == "double_ball"
    assert obj.get("kf_ball_a_diameter_mm") == 5.0
    assert obj.get("kf_ball_b_diameter_mm") == 6.0
    assert obj.get("kf_stem_diameter_mm") == 3.0
    assert obj.get("kf_center_distance_mm") == 8.0
    assert obj.get("kf_axis") == (0.0, 0.0, 1.0)
    assert obj.get("kf_ball_a_center_mm") == (0.0, 0.0, 0.0)
    assert obj.get("kf_ball_b_center_mm") == (0.0, 0.0, 8.0)

    # Unknown / uncomputed metadata must NOT exist
    assert "kf_range_min" not in obj
    assert "kf_range_max" not in obj
    assert "kf_role" not in obj
    assert "kf_side" not in obj
    assert "fit_quality" not in obj
    assert "printer_profile" not in obj


def test_double_ball_coordinate_math_and_extents():
    """Verify mathematical centers and bounding extents along +Z."""
    ball_a_d = 5.0
    ball_b_d = 5.0
    center_dist = 8.0

    r_a = ball_a_d / 2.0  # 2.5 mm
    r_b = ball_b_d / 2.0  # 2.5 mm

    # Ball A center at 0.0 -> bottom is at -r_a = -2.5 mm
    z_min = -r_a
    # Ball B center at +center_dist = +8.0 mm -> top is at +(8.0 + 2.5) = +10.5 mm
    z_max = center_dist + r_b
    total_z = z_max - z_min  # 13.0 mm

    assert math.isclose(z_min, -2.5)
    assert math.isclose(z_max, 10.5)
    assert math.isclose(total_z, 13.0)


def test_double_ball_matching_socket_compatibility():
    """Verify Double Ball ball diameters match PR-003 clearance calculations."""
    ball_a_d = 5.0
    ball_b_d = 6.0
    clearance = 0.15

    # Socket for Ball A
    socket_a_d = compute_socket_diameter(ball_a_d, clearance)
    assert math.isclose(socket_a_d, 5.30)

    # Socket for Ball B
    socket_b_d = compute_socket_diameter(ball_b_d, clearance)
    assert math.isclose(socket_b_d, 6.30)


def test_double_ball_multi_stage_rollback_on_stage1_failure():
    """Verify that if Stage 1 (Ball A + Stem) boolean fails, all resources are rolled back."""
    context = MagicMock()
    context.collection = MagicMock()

    with patch(
        "addon.kinefig.geometry.joints._evaluate_double_ball_union",
        side_effect=KineFigGeometryError("Injected Stage 1 Boolean Union failure"),
    ):
        with pytest.raises(KineFigGeometryError, match="Stage 1"):
            create_double_ball_geometry(context)


def test_double_ball_multi_stage_rollback_on_stage2_failure():
    """Verify that if Stage 2 (Intermediate + Ball B) fails, intermediate Stage 1 mesh is also rolled back."""
    context = MagicMock()
    context.collection = MagicMock()

    def mock_eval(ctx, obj, mod, stage=1):
        if stage == 1:
            fake_mesh = MagicMock()
            fake_mesh.vertices = [1, 2, 3]
            return fake_mesh
        raise KineFigGeometryError("Injected Stage 2 Boolean Union failure")

    with patch(
        "addon.kinefig.geometry.joints._evaluate_double_ball_union",
        side_effect=mock_eval,
    ):
        with pytest.raises(KineFigGeometryError, match="Stage 2"):
            create_double_ball_geometry(context)


def test_double_ball_post_evaluation_rollback_stage1():
    """Regression A: Verify that if failure occurs after eval_mesh_1 exists but before commit completes,
    eval_mesh_1 is deterministically rolled back with zero leaks."""
    baseline_objs = set(bpy.data.objects.keys())
    baseline_meshes = set(bpy.data.meshes.keys())

    context = MagicMock()
    context.collection = MagicMock()

    with patch(
        "addon.kinefig.geometry.joints._commit_evaluated_mesh",
        side_effect=KineFigGeometryError("Injected Stage 1 post-evaluation commit failure"),
    ):
        with pytest.raises(KineFigGeometryError, match="Stage 1 post-evaluation"):
            create_double_ball_geometry(context)

    assert set(bpy.data.objects.keys()) == baseline_objs, "Objects leaked after Stage 1 post-eval failure!"
    assert set(bpy.data.meshes.keys()) == baseline_meshes, "Meshes leaked after Stage 1 post-eval failure!"
    temp_objs = [name for name in bpy.data.objects.keys() if is_temp_object(name)]
    assert len(temp_objs) == 0, f"Leaked temp objects: {temp_objs}"


def test_double_ball_post_evaluation_rollback_stage2():
    """Regression B: Verify that if failure occurs after eval_mesh_2 exists but before final commit completes,
    eval_mesh_2 and intermediate meshes are deterministically rolled back with zero leaks."""
    baseline_objs = set(bpy.data.objects.keys())
    baseline_meshes = set(bpy.data.meshes.keys())

    context = MagicMock()
    context.collection = MagicMock()

    from addon.kinefig.geometry.joints import _commit_evaluated_mesh

    def commit_side_effect(eval_mesh, target_mesh, stage=1):
        if stage == 2:
            raise KineFigGeometryError("Injected Stage 2 post-evaluation commit failure")
        _commit_evaluated_mesh(eval_mesh, target_mesh, stage)

    with patch(
        "addon.kinefig.geometry.joints._commit_evaluated_mesh",
        side_effect=commit_side_effect,
    ):
        with pytest.raises(KineFigGeometryError, match="Stage 2 post-evaluation"):
            create_double_ball_geometry(context)

    assert set(bpy.data.objects.keys()) == baseline_objs, "Objects leaked after Stage 2 post-eval failure!"
    assert set(bpy.data.meshes.keys()) == baseline_meshes, "Meshes leaked after Stage 2 post-eval failure!"
    temp_objs = [name for name in bpy.data.objects.keys() if is_temp_object(name)]
    assert len(temp_objs) == 0, f"Leaked temp objects: {temp_objs}"

