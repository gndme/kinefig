"""Unit tests for female socket cavity geometry core."""

from unittest.mock import MagicMock, patch
import pytest
import bpy
from addon.kinefig.core.naming import get_next_object_name, is_temp_object
from addon.kinefig.core.errors import KineFigGeometryError
from addon.kinefig.geometry.sockets import create_ball_socket_geometry


def test_ball_socket_sequential_naming():
    """Verify ball socket object names allocate sequentially without collisions."""
    existing = []
    name1 = get_next_object_name("Socket", detail="Ball", existing_names=existing)
    assert name1 == "KF_Socket_Ball_001"

    existing.append(name1)
    name2 = get_next_object_name("Socket", detail="Ball", existing_names=existing)
    assert name2 == "KF_Socket_Ball_002"

    existing.append(name2)
    name3 = get_next_object_name("Socket", detail="Ball", existing_names=existing)
    assert name3 == "KF_Socket_Ball_003"


def test_ball_socket_factual_metadata_and_absence_of_unknowns():
    """Verify factual socket metadata is stored and uncomputed keys are strictly absent."""
    context = MagicMock()
    context.collection = MagicMock()
    context.scene.cursor.location = (0.0, 0.0, 0.0)

    eval_mesh_mock = MagicMock()
    eval_mesh_mock.vertices = [1, 2, 3, 4]
    bpy.data.meshes.new_from_object = MagicMock(return_value=eval_mesh_mock)

    obj = create_ball_socket_geometry(
        context=context,
        ball_diameter_mm=5.0,
        clearance_mm=0.15,
        socket_depth_mm=3.5,
    )

    # Factual metadata must exist
    assert obj.get("kf_type") == "socket"
    assert obj.get("kf_socket_type") == "ball"
    assert obj.get("kf_ball_diameter_mm") == 5.0
    assert obj.get("kf_clearance_mm") == 0.15
    assert obj.get("kf_socket_diameter_mm") == 5.30
    assert obj.get("kf_socket_depth_mm") == 3.5
    assert obj.get("kf_axis") == (0.0, 0.0, 1.0)
    assert obj.get("kf_insertion_axis") == (0.0, 0.0, 1.0)
    assert obj.get("kf_opening_normal") == (0.0, 0.0, -1.0)

    # Unknown / uncomputed metadata must NOT exist
    assert "kf_range_min" not in obj
    assert "kf_range_max" not in obj
    assert "kf_role" not in obj
    assert "kf_side" not in obj
    assert "fit_quality" not in obj
    assert "printer_profile" not in obj


def test_ball_socket_transactional_rollback_on_boolean_failure():
    """Verify Boolean trimming failure triggers full rollback of all allocated resources."""
    # Pre-existing unrelated scene object that must survive untouched
    unrelated = bpy.data.objects.new("User_Mesh")

    context = MagicMock()
    context.collection = MagicMock()
    context.scene.cursor.location = (0.0, 0.0, 0.0)

    # Trigger failure via internal seam patch
    with patch(
        "addon.kinefig.geometry.sockets._evaluate_boolean_trim",
        side_effect=KineFigGeometryError("Injected Boolean trimming failure for transactional rollback test"),
    ):
        with pytest.raises(KineFigGeometryError, match="Injected Boolean trimming failure"):
            create_ball_socket_geometry(
                context=context,
                ball_diameter_mm=5.0,
                clearance_mm=0.15,
                socket_depth_mm=3.5,
            )

    # Assert that no partial socket or temp objects remain
    remaining_names = [o.name for o in bpy.data.objects]
    assert remaining_names == ["User_Mesh"], f"Orphan objects found: {remaining_names}"

    # Assert no temp mesh datablocks remain
    temp_meshes = [m.name for m in bpy.data.meshes if is_temp_object(m.name)]
    assert len(temp_meshes) == 0, f"Orphan temp meshes found: {temp_meshes}"
