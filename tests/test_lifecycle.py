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


def test_smoke_operator_execution_and_repeated_naming():
    """Verify smoke operator creates 10mm sphere with deterministic sequential naming."""
    op = KINEFIG_OT_create_smoke_object()
    op.report = MagicMock()

    bpy.ops.mesh = MagicMock()
    bpy.ops.mesh.primitive_uv_sphere_add = MagicMock()

    # First execution: scene has no smoke ball
    bpy.data.objects = []
    context1 = MagicMock()
    obj1 = MockBlenderObject()
    context1.active_object = obj1

    result1 = op.execute(context1)
    assert result1 == {"FINISHED"}
    assert obj1.name == "KF_Smoke_Ball_001"
    assert obj1["kf_type"] == "smoke"

    # Second execution: scene has obj1 ("KF_Smoke_Ball_001")
    bpy.data.objects = [obj1]
    context2 = MagicMock()
    obj2 = MockBlenderObject()
    context2.active_object = obj2

    result2 = op.execute(context2)
    assert result2 == {"FINISHED"}
    assert obj2.name == "KF_Smoke_Ball_002"
    assert obj1.name == "KF_Smoke_Ball_001"  # Not overwritten or renamed


def test_ball_joint_operator_execution_and_metadata():
    """Verify ball joint operator creates joint with correct naming and metadata."""
    op = KINEFIG_OT_create_ball_joint()
    op.report = MagicMock()
    op.ball_diameter_mm = 5.0
    op.stem_diameter_mm = 3.0
    op.stem_length_mm = 5.0
    op.segments = 32
    op.rings = 16

    bpy.data.objects = MockObjectsCollection()
    bpy.data.meshes = MagicMock()
    bpy.data.meshes.new = MagicMock()

    context = MagicMock()
    context.scene.cursor.location = (0.0, 0.0, 0.0)
    context.collection = MagicMock()

    result = op.execute(context)
    assert result == {"FINISHED"}
    assert op.report.called

    # Verify object created and named KF_Joint_Ball_001
    created_names = [o.name for o in bpy.data.objects]
    assert "KF_Joint_Ball_001" in created_names


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
