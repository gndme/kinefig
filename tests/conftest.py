"""Pytest configuration and mocks for headless/standalone test execution.

When running outside Blender, bpy is not available. This conftest provides
a mock bpy and bmesh module so that add-on code, registration, and unit tests
can be verified in standard CI/CD and local environments.
"""

import sys
from unittest.mock import MagicMock
import pytest


class MockCollection:
    """Mock collection for bpy.data.objects and bpy.data.meshes."""

    def __init__(self):
        self._items = {}

    def new(self, name, *args, **kwargs):
        mock_item = MagicMock()
        mock_item.name = name
        mock_item.properties = {}
        mock_item.modifiers = MagicMock()
        mock_item.data = MagicMock()
        mock_item.location = (0.0, 0.0, 0.0)
        mock_item.__getitem__ = lambda slf, k: slf.properties[k]
        mock_item.__setitem__ = lambda slf, k, v: slf.properties.__setitem__(k, v)
        mock_item.__contains__ = lambda slf, k: k in slf.properties
        mock_item.get = lambda k, d=None: mock_item.properties.get(k, d)
        self._items[name] = mock_item
        return mock_item

    def remove(self, item, do_unlink=True):
        name = getattr(item, "name", str(item))
        if name in self._items:
            del self._items[name]
        else:
            for k, v in list(self._items.items()):
                if v == item:
                    del self._items[k]

    def get(self, name, default=None):
        return self._items.get(name, default)

    def __iter__(self):
        return iter(list(self._items.values()))

    def __len__(self):
        return len(self._items)

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self._items
        return item in self._items.values()

    def keys(self):
        return self._items.keys()

    def values(self):
        return self._items.values()

    def clear(self):
        self._items.clear()


if "bpy" not in sys.modules:
    mock_bpy = MagicMock()

    class MockOperator:
        """Mock base class for bpy.types.Operator."""
        bl_idname = ""
        bl_label = ""
        bl_description = ""
        bl_options = set()

        def report(self, type_set, message):
            pass

    class MockPanel:
        """Mock base class for bpy.types.Panel."""
        bl_label = ""
        bl_idname = ""
        bl_space_type = ""
        bl_region_type = ""
        bl_category = ""

    class MockPropertyGroup:
        """Mock base class for bpy.types.PropertyGroup."""
        pass

    def mock_prop(*args, **kwargs):
        return None

    mock_bpy.types.Operator = MockOperator
    mock_bpy.types.Panel = MockPanel
    mock_bpy.types.PropertyGroup = MockPropertyGroup
    mock_bpy.props.StringProperty = mock_prop
    mock_bpy.props.FloatProperty = mock_prop
    mock_bpy.props.IntProperty = mock_prop
    mock_bpy.props.BoolProperty = mock_prop
    mock_bpy.props.EnumProperty = mock_prop
    mock_bpy.props.PointerProperty = mock_prop
    mock_bpy.path.abspath = lambda p: p
    mock_bpy.utils.register_class = MagicMock()
    mock_bpy.utils.unregister_class = MagicMock()

    mock_bpy.data.objects = MockCollection()
    mock_bpy.data.meshes = MockCollection()

    sys.modules["bpy"] = mock_bpy

if "bmesh" not in sys.modules:
    mock_bmesh = MagicMock()
    mock_bm_instance = MagicMock()
    mock_bmesh.new.return_value = mock_bm_instance
    sys.modules["bmesh"] = mock_bmesh


@pytest.fixture(autouse=True)
def reset_mock_bpy():
    """Reset mock bpy.data collections before every test."""
    if "bpy" in sys.modules and isinstance(sys.modules["bpy"], MagicMock):
        sys.modules["bpy"].data.objects = MockCollection()
        sys.modules["bpy"].data.meshes = MockCollection()
        mock_eval_mesh = MagicMock()
        mock_eval_mesh.vertices = [1, 2, 3]
        sys.modules["bpy"].data.meshes.new_from_object = MagicMock(return_value=mock_eval_mesh)
