"""Lifecycle and operator tests for KineFig add-on."""

from unittest.mock import MagicMock
import bpy
import addon.kinefig as kinefig
from addon.kinefig.operators.smoke import KINEFIG_OT_create_smoke_object
from addon.kinefig.operators.joints import KINEFIG_OT_create_ball_joint
from addon.kinefig.operators.diagnostics import (
    KINEFIG_OT_copy_debug_info,
    KINEFIG_OT_export_diagnostic_report,
    KINEFIG_OT_report_bug,
)


class MockBlenderObject:
    """Mock Blender Object supporting custom properties and attributes."""

    def __init__(self, name=""):
        self.name = name
        self.properties = {}
        self.location = (0.0, 0.0, 0.0)
        self.data = MagicMock()
        self.modifiers = MagicMock()

    def __getitem__(self, key):
        return self.properties[key]

    def __setitem__(self, key, value):
        self.properties[key] = value

    def get(self, key, default=None):
        return self.properties.get(key, default)

    def select_set(self, state):
        pass


class MockObjectsCollection(list):
    """Mock objects collection supporting both iteration and .new()."""

    def new(self, name, mesh):
        obj = MockBlenderObject(name)
        self.append(obj)
        return obj

    def remove(self, obj, do_unlink=True):
        if obj in self:
            super().remove(obj)


def test_register_and_unregister():
    """Verify register and unregister register/unregister all classes in expected order."""
    bpy.utils.register_class.reset_mock()
    bpy.utils.unregister_class.reset_mock()

    kinefig.register()
    assert bpy.utils.register_class.call_count == len(kinefig._CLASSES)
    registered_classes = [c.args[0] for c in bpy.utils.register_class.call_args_list]
    assert registered_classes == list(kinefig._CLASSES)

    kinefig.unregister()
    assert bpy.utils.unregister_class.call_count == len(kinefig._CLASSES)
    unregistered_classes = [c.args[0] for c in bpy.utils.unregister_class.call_args_list]
    assert unregistered_classes == list(reversed(kinefig._CLASSES))


def test_smoke_operator_poll():
    """Verify smoke operator poll allows execution only in Object Mode."""
    context_obj_mode = MagicMock()
    context_obj_mode.mode = "OBJECT"
    assert KINEFIG_OT_create_smoke_object.poll(context_obj_mode) is True

    context_edit_mode = MagicMock()
    context_edit_mode.mode = "EDIT_MESH"
    assert KINEFIG_OT_create_smoke_object.poll(context_edit_mode) is False


def test_ball_joint_operator_poll():
    """Verify ball joint operator poll allows execution only in Object Mode."""
    context_obj_mode = MagicMock()
    context_obj_mode.mode = "OBJECT"
    assert KINEFIG_OT_create_ball_joint.poll(context_obj_mode) is True

    context_edit_mode = MagicMock()
    context_edit_mode.mode = "EDIT_MESH"
    assert KINEFIG_OT_create_ball_joint.poll(context_edit_mode) is False


def test_ball_socket_operator_poll():
    """Verify ball socket operator poll allows execution only in Object Mode."""
    from addon.kinefig.operators.sockets import KINEFIG_OT_create_ball_socket

    context_obj_mode = MagicMock()
    context_obj_mode.mode = "OBJECT"
    assert KINEFIG_OT_create_ball_socket.poll(context_obj_mode) is True

    context_edit_mode = MagicMock()
    context_edit_mode.mode = "EDIT_MESH"
    assert KINEFIG_OT_create_ball_socket.poll(context_edit_mode) is False



def test_smoke_operator_execution_and_repeated_naming():
    """Verify smoke operator creates 10mm sphere with deterministic sequential naming."""
    op = KINEFIG_OT_create_smoke_object()
    op.report = MagicMock()

    bpy.ops.mesh = MagicMock()
    bpy.ops.mesh.primitive_uv_sphere_add = MagicMock()

    # First execution: scene has no smoke ball
    bpy.data.objects.clear()
    context1 = MagicMock()
    obj1 = MockBlenderObject()
    context1.active_object = obj1

    result1 = op.execute(context1)
    assert result1 == {"FINISHED"}
    assert obj1.name == "KF_Smoke_Ball_001"
    assert obj1["kf_type"] == "smoke"

    # Second execution: scene has obj1 ("KF_Smoke_Ball_001")
    bpy.data.objects.clear()
    bpy.data.objects.new("KF_Smoke_Ball_001")
    context2 = MagicMock()
    obj2 = MockBlenderObject()
    context2.active_object = obj2

    result2 = op.execute(context2)
    assert result2 == {"FINISHED"}
    assert obj2.name == "KF_Smoke_Ball_002"


def test_ball_joint_operator_execution_and_metadata():
    """Verify ball joint operator creates joint with correct naming and metadata."""
    op = KINEFIG_OT_create_ball_joint()
    op.report = MagicMock()
    op.ball_diameter_mm = 5.0
    op.stem_diameter_mm = 3.0
    op.stem_length_mm = 5.0
    op.segments = 32
    op.rings = 16

    context = MagicMock()
    context.scene.cursor.location = (0.0, 0.0, 0.0)
    context.collection = MagicMock()

    result = op.execute(context)
    assert result == {"FINISHED"}
    assert op.report.called

    # Verify object created and named KF_Joint_Ball_001
    created_names = [o.name for o in bpy.data.objects]
    assert "KF_Joint_Ball_001" in created_names



def test_ball_joint_operator_validation_failure():
    """Verify operator returns CANCELLED and reports error on invalid parameters."""
    op = KINEFIG_OT_create_ball_joint()
    op.report = MagicMock()
    op.ball_diameter_mm = 5.0
    op.stem_diameter_mm = 5.0  # Invalid: stem >= ball
    op.stem_length_mm = 5.0
    op.segments = 32
    op.rings = 16

    context = MagicMock()
    result = op.execute(context)
    assert result == {"CANCELLED"}
    op.report.assert_called_once()
    assert "ERROR" in op.report.call_args[0][0]


def test_ball_joint_operator_geometry_failure():
    """Verify operator returns CANCELLED and reports error when geometry creation fails."""
    from unittest.mock import patch
    from addon.kinefig.core.errors import KineFigGeometryError

    op = KINEFIG_OT_create_ball_joint()
    op.report = MagicMock()
    op.ball_diameter_mm = 5.0
    op.stem_diameter_mm = 3.0
    op.stem_length_mm = 5.0
    op.segments = 32
    op.rings = 16

    context = MagicMock()
    with patch(
        "addon.kinefig.operators.joints.create_ball_joint_geometry",
        side_effect=KineFigGeometryError("Simulated boolean engine failure"),
    ):
        result = op.execute(context)
        assert result == {"CANCELLED"}
        op.report.assert_called_once()
        assert "ERROR" in op.report.call_args[0][0]
        assert "Geometry error" in str(op.report.call_args[0][1])
def test_ball_socket_operator_execution_and_metadata():
    """Verify ball socket operator creates socket with correct naming and metadata."""
    from addon.kinefig.operators.sockets import KINEFIG_OT_create_ball_socket

    op = KINEFIG_OT_create_ball_socket()
    op.report = MagicMock()
    op.ball_diameter_mm = 5.0
    op.clearance_mm = 0.15
    op.socket_depth_mm = 3.5
    op.segments = 32
    op.rings = 16

    context = MagicMock()
    context.scene.cursor.location = (0.0, 0.0, 0.0)
    context.collection = MagicMock()

    result = op.execute(context)
    assert result == {"FINISHED"}
    assert op.report.called

    created_names = [o.name for o in bpy.data.objects]
    assert "KF_Socket_Ball_001" in created_names


def test_ball_socket_operator_validation_failure():
    """Verify socket operator returns CANCELLED on invalid depth >= diameter."""
    from addon.kinefig.operators.sockets import KINEFIG_OT_create_ball_socket

    op = KINEFIG_OT_create_ball_socket()
    op.report = MagicMock()
    op.ball_diameter_mm = 5.0
    op.clearance_mm = 0.15
    op.socket_depth_mm = 6.0  # Invalid: depth >= diameter (5.30mm)

    context = MagicMock()
    result = op.execute(context)
    assert result == {"CANCELLED"}
    op.report.assert_called_once()
    assert "ERROR" in op.report.call_args[0][0]


def test_ball_socket_operator_geometry_failure():
    """Verify socket operator returns CANCELLED when geometry creation raises KineFigGeometryError."""
    from unittest.mock import patch
    from addon.kinefig.operators.sockets import KINEFIG_OT_create_ball_socket
    from addon.kinefig.core.errors import KineFigGeometryError

    op = KINEFIG_OT_create_ball_socket()
    op.report = MagicMock()
    op.ball_diameter_mm = 5.0
    op.clearance_mm = 0.15
    op.socket_depth_mm = 3.5
    op.segments = 32
    op.rings = 16

    context = MagicMock()
    with patch(
        "addon.kinefig.operators.sockets.create_ball_socket_geometry",
        side_effect=KineFigGeometryError("Simulated boolean trimming engine failure"),
    ):
        result = op.execute(context)
        assert result == {"CANCELLED"}
        op.report.assert_called_once()
        assert "ERROR" in op.report.call_args[0][0]
        assert "Geometry error" in str(op.report.call_args[0][1])


def test_use_selected_ball_operator():
    """Verify use_selected_ball copies ball diameter from active ball joint."""
    from addon.kinefig.operators.sockets import KINEFIG_OT_use_selected_ball

    op = KINEFIG_OT_use_selected_ball()
    op.report = MagicMock()

    # Context without valid ball joint -> poll is False
    ctx_invalid = MagicMock()
    ctx_invalid.active_object = None
    assert not KINEFIG_OT_use_selected_ball.poll(ctx_invalid)

    unrelated = MagicMock()
    unrelated.get.return_value = None
    ctx_invalid.active_object = unrelated
    assert not KINEFIG_OT_use_selected_ball.poll(ctx_invalid)

    # Context with valid ball joint -> poll is True and execute copies value
    ball_obj = MagicMock()
    ball_props = {
        "kf_type": "joint",
        "kf_joint_type": "ball",
        "kf_ball_diameter_mm": 6.5,
    }
    ball_obj.name = "KF_Joint_Ball_001"
    ball_obj.get.side_effect = lambda k, d=None: ball_props.get(k, d)
    ball_obj.__contains__ = lambda self, k: k in ball_props

    ctx_valid = MagicMock()
    ctx_valid.active_object = ball_obj
    ctx_valid.scene.kinefig_ball_socket.ball_diameter_mm = 5.0

    assert KINEFIG_OT_use_selected_ball.poll(ctx_valid)

    res = op.execute(ctx_valid)
    assert res == {"FINISHED"}
    assert ctx_valid.scene.kinefig_ball_socket.ball_diameter_mm == 6.5
    op.report.assert_called_once()
    assert "INFO" in op.report.call_args[0][0]


import pytest


@pytest.mark.parametrize(
    "invalid_val",
    [
        0,
        0.0,
        -1,
        -5.0,
        float("nan"),
        float("inf"),
        float("-inf"),
        "abc",
        None,
    ],
)
def test_use_selected_ball_invalid_metadata_rejected(invalid_val):
    """Verify operator returns CANCELLED and does NOT mutate scene settings for invalid metadata."""
    from addon.kinefig.operators.sockets import KINEFIG_OT_use_selected_ball

    op = KINEFIG_OT_use_selected_ball()
    op.report = MagicMock()

    ball_obj = MagicMock()
    ball_props = {
        "kf_type": "joint",
        "kf_joint_type": "ball",
        "kf_ball_diameter_mm": invalid_val,
    }
    ball_obj.name = "KF_Joint_Ball_Corrupted"
    ball_obj.get.side_effect = lambda k, d=None: ball_props.get(k, d)
    ball_obj.__contains__ = lambda self, k: k in ball_props

    ctx = MagicMock()
    ctx.active_object = ball_obj
    initial_setting = 5.0
    ctx.scene.kinefig_ball_socket.ball_diameter_mm = initial_setting

    res = op.execute(ctx)
    assert res == {"CANCELLED"}
    assert ctx.scene.kinefig_ball_socket.ball_diameter_mm == initial_setting
    op.report.assert_called_once()
    assert "ERROR" in op.report.call_args[0][0]


def test_copy_debug_info_operator():
    """Verify copy debug info operator copies text to clipboard."""
    op = KINEFIG_OT_copy_debug_info()
    op.report = MagicMock()
    context = MagicMock()
    context.window_manager.clipboard = ""

    res = op.execute(context)
    assert res == {"FINISHED"}
    assert "KineFig:" in context.window_manager.clipboard
    op.report.assert_called_once()
