"""Lifecycle and operator tests for KineFig add-on."""

from unittest.mock import MagicMock
import bpy
import addon.kinefig as kinefig
from addon.kinefig.operators.smoke import KINEFIG_OT_create_smoke_object


class MockBlenderObject:
    """Mock Blender Object supporting custom properties and attributes."""

    def __init__(self, name=""):
        self.name = name
        self.properties = {}

    def __getitem__(self, key):
        return self.properties[key]

    def __setitem__(self, key, value):
        self.properties[key] = value


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


def test_smoke_operator_execution():
    """Verify smoke operator creates 10mm sphere with correct naming and metadata."""
    op = KINEFIG_OT_create_smoke_object()
    op.report = MagicMock()

    context = MagicMock()
    mock_obj = MockBlenderObject()
    context.active_object = mock_obj

    bpy.ops.mesh = MagicMock()
    bpy.ops.mesh.primitive_uv_sphere_add = MagicMock()

    result = op.execute(context)

    assert result == {"FINISHED"}
    # 5mm radius = 0.005m
    bpy.ops.mesh.primitive_uv_sphere_add.assert_called_once_with(radius=0.005)
    assert mock_obj.name == "KF_Smoke_Ball_001"
    assert mock_obj["kf_type"] == "smoke"
    op.report.assert_called_once()
