"""Pytest configuration and mocks for headless/standalone test execution.

When running outside Blender, bpy is not available. This conftest provides
a mock bpy and bmesh module so that add-on code, registration, and unit tests
can be verified in standard CI/CD and local environments.
"""

import sys
from unittest.mock import MagicMock

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

    sys.modules["bpy"] = mock_bpy

if "bmesh" not in sys.modules:
    mock_bmesh = MagicMock()
    mock_bm_instance = MagicMock()
    mock_bmesh.new.return_value = mock_bm_instance
    sys.modules["bmesh"] = mock_bmesh
