"""Unit tests for PR-005 Parametric Peg and Peg Socket Core."""

import math
from unittest.mock import MagicMock
import pytest
import bpy

from addon.kinefig.core.units import mm_to_blender
from addon.kinefig.core.naming import get_next_object_name
from addon.kinefig.core.clearance import compute_socket_diameter
from addon.kinefig.core.errors import KineFigGeometryError
from addon.kinefig.geometry.joints import create_peg_geometry
from addon.kinefig.geometry.sockets import create_peg_socket_geometry
from addon.kinefig.ui.panel import (
    _get_valid_selected_peg_diameter,
    _get_valid_selected_ball_diameter,
    KINEFIG_PT_main,
)
from addon.kinefig.operators.sockets import KINEFIG_OT_use_selected_peg


def test_peg_unit_conversions():
    """Verify millimeter to Blender meter conversions for peg dimensions."""
    # 3.0 mm peg diameter = 0.003 m, radius = 0.0015 m
    assert mm_to_blender(3.0) == 0.003
    assert mm_to_blender(3.0) / 2.0 == 0.0015

    # 5.0 mm peg length = 0.005 m
    assert mm_to_blender(5.0) == 0.005


def test_peg_taper_math():
    """Verify taper calculations for draft angles."""
    r_base_m = mm_to_blender(3.0 / 2.0)  # 0.0015 m
    length_m = mm_to_blender(5.0)        # 0.005 m

    # 0 degree draft -> straight cylinder
    taper_rad_0 = math.radians(0.0)
    r_tip_0 = r_base_m - length_m * math.tan(taper_rad_0)
    assert r_tip_0 == r_base_m

    # 5 degree draft -> narrower tip
    taper_rad_5 = math.radians(5.0)
    r_tip_5 = r_base_m - length_m * math.tan(taper_rad_5)
    assert 0 < r_tip_5 < r_base_m
    tip_diam_mm = r_tip_5 * 2000.0
    expected_tip_mm = 3.0 - 2.0 * 5.0 * math.tan(math.radians(5.0))
    assert math.isclose(tip_diam_mm, expected_tip_mm, rel_tol=1e-5)


def test_peg_sequential_naming():
    """Verify peg object names allocate sequentially without collisions."""
    existing = []
    name1 = get_next_object_name("Joint", detail="Peg", existing_names=existing)
    assert name1 == "KF_Joint_Peg_001"
    existing.append(name1)

    name2 = get_next_object_name("Joint", detail="Peg", existing_names=existing)
    assert name2 == "KF_Joint_Peg_002"
    existing.append(name2)

    name3 = get_next_object_name("Joint", detail="Peg", existing_names=existing)
    assert name3 == "KF_Joint_Peg_003"


def test_peg_socket_sequential_naming():
    """Verify peg socket object names allocate sequentially without collisions."""
    existing = []
    name1 = get_next_object_name("Socket", detail="Peg", existing_names=existing)
    assert name1 == "KF_Socket_Peg_001"
    existing.append(name1)

    name2 = get_next_object_name("Socket", detail="Peg", existing_names=existing)
    assert name2 == "KF_Socket_Peg_002"


def test_peg_creation_mock():
    """Verify create_peg_geometry sets factual metadata and coordinates."""
    context = MagicMock()
    context.collection = MagicMock()
    context.collection.objects = MagicMock()

    obj = create_peg_geometry(
        context=context,
        peg_diameter_mm=3.0,
        peg_length_mm=5.0,
        taper_angle_deg=0.0,
        segments=32,
    )

    assert obj.name == "KF_Joint_Peg_001"
    assert obj.get("kf_type") == "joint"
    assert obj.get("kf_joint_type") == "peg"
    assert math.isclose(obj.get("kf_peg_diameter_mm"), 3.0)
    assert math.isclose(obj.get("kf_peg_length_mm"), 5.0)
    assert math.isclose(obj.get("kf_taper_angle_deg"), 0.0)
    assert tuple(obj.get("kf_axis")) == (0.0, 0.0, 1.0)

    # Check absence of uncomputed metadata
    for key in ("kf_role", "kf_side", "fit_quality", "printer_profile"):
        assert key not in obj


def test_peg_socket_creation_mock():
    """Verify create_peg_socket_geometry sets factual metadata and coordinates."""
    context = MagicMock()
    context.collection = MagicMock()
    context.collection.objects = MagicMock()

    obj = create_peg_socket_geometry(
        context=context,
        peg_diameter_mm=3.0,
        radial_clearance_mm=0.15,
        socket_depth_mm=5.0,
        segments=32,
    )

    assert obj.name == "KF_Socket_Peg_001"
    assert obj.get("kf_type") == "socket"
    assert obj.get("kf_socket_type") == "peg"
    assert math.isclose(obj.get("kf_peg_diameter_mm"), 3.0)
    assert math.isclose(obj.get("kf_radial_clearance_mm"), 0.15)
    assert math.isclose(obj.get("kf_socket_diameter_mm"), 3.30)
    assert math.isclose(obj.get("kf_socket_depth_mm"), 5.0)
    assert tuple(obj.get("kf_axis")) == (0.0, 0.0, 1.0)
    assert tuple(obj.get("kf_insertion_axis")) == (0.0, 0.0, 1.0)
    assert tuple(obj.get("kf_opening_normal")) == (0.0, 0.0, -1.0)

    # Check absence of uncomputed metadata
    for key in ("kf_role", "kf_side", "fit_quality", "printer_profile"):
        assert key not in obj


def test_peg_clearance_matching_invariant():
    """Verify peg diameter and clearance mathematics match nominal receiver."""
    peg_d = 3.0
    clearance = 0.15
    socket_d = compute_socket_diameter(peg_d, clearance)
    assert math.isclose(socket_d, 3.30)

    # Invariant: socket radius - peg radius == radial clearance
    peg_r = peg_d / 2.0
    socket_r = socket_d / 2.0
    assert math.isclose(socket_r - peg_r, clearance, abs_tol=1e-7)


def test_peg_rollback_on_failure():
    """Verify transactional rollback cleans up if peg creation fails."""
    baseline_objs = set(bpy.data.objects.keys())
    baseline_meshes = set(bpy.data.meshes.keys())

    context = MagicMock()
    context.collection = MagicMock()
    # Force failure when linking object
    context.collection.objects.link.side_effect = RuntimeError("Collection link failed")

    with pytest.raises(KineFigGeometryError, match="Failed to create peg joint"):
        create_peg_geometry(context=context)

    assert set(bpy.data.objects.keys()) == baseline_objs
    assert set(bpy.data.meshes.keys()) == baseline_meshes


def test_peg_socket_rollback_on_failure():
    """Verify transactional rollback cleans up if peg socket creation fails."""
    baseline_objs = set(bpy.data.objects.keys())
    baseline_meshes = set(bpy.data.meshes.keys())

    context = MagicMock()
    context.collection = MagicMock()
    context.collection.objects.link.side_effect = RuntimeError("Collection link failed")

    with pytest.raises(KineFigGeometryError, match="Failed to create peg socket"):
        create_peg_socket_geometry(context=context)

    assert set(bpy.data.objects.keys()) == baseline_objs
    assert set(bpy.data.meshes.keys()) == baseline_meshes


@pytest.mark.parametrize(
    "malformed_val",
    [
        "abc",
        None,
        float("nan"),
        float("inf"),
        float("-inf"),
        0,
        0.0,
        -1,
        -5.0,
    ],
)
def test_get_valid_selected_peg_diameter_malformed(malformed_val):
    """Verify _get_valid_selected_peg_diameter returns None on all malformed metadata values."""
    mock_obj = {
        "kf_type": "joint",
        "kf_joint_type": "peg",
        "kf_peg_diameter_mm": malformed_val,
    }
    assert _get_valid_selected_peg_diameter(mock_obj) is None


def test_get_valid_selected_peg_diameter_valid():
    """Verify _get_valid_selected_peg_diameter returns float on valid positive finite metadata."""
    mock_obj = {
        "kf_type": "joint",
        "kf_joint_type": "peg",
        "kf_peg_diameter_mm": 3.0,
    }
    assert _get_valid_selected_peg_diameter(mock_obj) == 3.0

    mock_obj["kf_peg_diameter_mm"] = 4.5
    assert _get_valid_selected_peg_diameter(mock_obj) == 4.5


def test_get_valid_selected_peg_diameter_non_peg_or_missing():
    """Verify _get_valid_selected_peg_diameter returns None for non-peg objects or missing metadata."""
    assert _get_valid_selected_peg_diameter(None) is None
    assert _get_valid_selected_peg_diameter({}) is None
    assert _get_valid_selected_peg_diameter({"kf_type": "socket"}) is None
    assert _get_valid_selected_peg_diameter({"kf_type": "joint", "kf_joint_type": "ball"}) is None
    assert _get_valid_selected_peg_diameter({"kf_type": "joint", "kf_joint_type": "peg"}) is None


@pytest.mark.parametrize(
    "malformed_val",
    [
        "abc",
        None,
        float("nan"),
        float("inf"),
        float("-inf"),
        0,
        0.0,
        -1,
        -5.0,
    ],
)
def test_get_valid_selected_ball_diameter_malformed(malformed_val):
    """Verify _get_valid_selected_ball_diameter returns None on all malformed metadata values."""
    mock_obj = {
        "kf_type": "joint",
        "kf_joint_type": "ball",
        "kf_ball_diameter_mm": malformed_val,
    }
    assert _get_valid_selected_ball_diameter(mock_obj) is None


@pytest.mark.parametrize(
    "malformed_val",
    [
        "abc",
        None,
        float("nan"),
        float("inf"),
        float("-inf"),
        0,
        0.0,
        -1,
        -5.0,
    ],
)
def test_panel_draw_safe_with_malformed_peg_metadata(malformed_val):
    """Verify Panel.draw does not raise when active object has malformed peg metadata.

    Asserts:
    1. _get_valid_selected_peg_diameter returns None so invalid action is not presented.
    2. Panel.draw executes without exception.
    3. Existing scene socket settings are not mutated.
    """
    mock_obj = MagicMock()
    data = {
        "kf_type": "joint",
        "kf_joint_type": "peg",
        "kf_peg_diameter_mm": malformed_val,
    }
    mock_obj.get.side_effect = data.get
    mock_obj.name = "KF_Joint_Peg_Mock"

    # Context mock
    context = MagicMock()
    context.active_object = mock_obj

    # Scene mock with peg socket property
    scene = MagicMock()
    scene.kinefig_peg_socket = MagicMock()
    scene.kinefig_peg_socket.peg_diameter_mm = 3.0
    scene.kinefig_peg_socket.radial_clearance_mm = 0.15
    scene.kinefig_peg_socket.socket_depth_mm = 5.0
    scene.kinefig_peg_socket.segments = 32

    # Provide ball joint and socket scene props to avoid AttributeError in panel draw
    scene.kinefig_ball_joint = MagicMock()
    scene.kinefig_ball_joint.ball_diameter_mm = 5.0
    scene.kinefig_ball_joint.stem_diameter_mm = 3.0
    scene.kinefig_ball_joint.stem_length_mm = 5.0
    scene.kinefig_ball_joint.segments = 32
    scene.kinefig_ball_joint.rings = 16

    scene.kinefig_ball_socket = MagicMock()
    scene.kinefig_ball_socket.ball_diameter_mm = 5.0
    scene.kinefig_ball_socket.clearance_mm = 0.15
    scene.kinefig_ball_socket.socket_depth_mm = 3.5
    scene.kinefig_ball_socket.segments = 32
    scene.kinefig_ball_socket.rings = 16

    scene.kinefig_peg_joint = MagicMock()
    scene.kinefig_peg_joint.peg_diameter_mm = 3.0
    scene.kinefig_peg_joint.peg_length_mm = 5.0
    scene.kinefig_peg_joint.taper_angle_deg = 0.0
    scene.kinefig_peg_joint.segments = 32

    scene.kinefig_double_ball_joint = MagicMock()
    scene.kinefig_double_ball_joint.ball_a_diameter_mm = 5.0
    scene.kinefig_double_ball_joint.ball_b_diameter_mm = 5.0
    scene.kinefig_double_ball_joint.stem_diameter_mm = 3.0
    scene.kinefig_double_ball_joint.center_distance_mm = 8.0
    scene.kinefig_double_ball_joint.segments = 32
    scene.kinefig_double_ball_joint.rings = 16

    context.scene = scene

    panel = KINEFIG_PT_main()
    panel.layout = MagicMock()
    panel.layout.box.return_value = MagicMock()

    # Must NOT raise exception during draw
    panel.draw(context)

    # Valid diameter must be None
    assert _get_valid_selected_peg_diameter(mock_obj) is None

    # Scene socket settings must remain completely unchanged
    assert scene.kinefig_peg_socket.peg_diameter_mm == 3.0


@pytest.mark.parametrize(
    "malformed_val",
    [
        "abc",
        None,
        float("nan"),
        float("inf"),
        float("-inf"),
        0,
        0.0,
        -1,
        -5.0,
    ],
)
def test_use_selected_peg_operator_rejection(malformed_val):
    """Verify KINEFIG_OT_use_selected_peg safely cancels and preserves scene settings."""
    op = KINEFIG_OT_use_selected_peg()
    reports = []
    op.report = lambda level, msg: reports.append((level, msg))

    mock_obj = MagicMock()
    data = {
        "kf_type": "joint",
        "kf_joint_type": "peg",
        "kf_peg_diameter_mm": malformed_val,
    }
    mock_obj.get.side_effect = data.get
    mock_obj.name = "KF_Joint_Peg_Mock"

    context = MagicMock()
    context.active_object = mock_obj
    context.scene = MagicMock()
    context.scene.kinefig_peg_socket = MagicMock()
    context.scene.kinefig_peg_socket.peg_diameter_mm = 3.0

    res = op.execute(context)
    assert res == {"CANCELLED"}
    # Scene setting must NOT be modified
    assert context.scene.kinefig_peg_socket.peg_diameter_mm == 3.0
    assert any("WARNING" in r[0] for r in reports)

