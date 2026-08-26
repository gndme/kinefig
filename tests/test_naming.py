"""Unit tests for core/naming.py."""

import pytest
from addon.kinefig.core.naming import (
    PREFIX_KINEFIG,
    PREFIX_TEMP,
    format_object_name,
    format_temp_name,
    is_kinefig_object,
    is_temp_object,
    sanitize_filename,
)


def test_naming_prefixes():
    """Verify standard prefixes comply with AGENTS.md."""
    assert PREFIX_KINEFIG == "KF_"
    assert PREFIX_TEMP == "_KF_TMP_"


def test_format_object_name_variations():
    """Verify object name formatting patterns."""
    assert format_object_name("Joint", "Ball", index=1) == "KF_Joint_Ball_001"
    assert format_object_name("Joint", "DoubleBall", index=2) == "KF_Joint_DoubleBall_002"
    assert format_object_name("Socket", index=1) == "KF_Socket_001"
    assert format_object_name("SplitPlane", index=1) == "KF_SplitPlane_001"
    assert format_object_name("FigurePart", "UpperArm", side="L") == "KF_FigurePart_L_UpperArm"
    assert format_object_name("FigurePart", "Forearm", side="r", index=1) == "KF_FigurePart_R_Forearm_001"
    assert format_object_name("Smoke", "Ball", index=1) == "KF_Smoke_Ball_001"


def test_format_temp_name():
    """Verify temporary object names use temp prefix."""
    assert format_temp_name("Cutter", index=1) == "_KF_TMP_Cutter_001"
    assert format_temp_name("BooleanHelper") == "_KF_TMP_BooleanHelper"


def test_is_kinefig_object():
    """Verify detection of KineFig generated objects."""
    assert is_kinefig_object("KF_Joint_Ball_001") is True
    assert is_kinefig_object("KF_Socket_001") is True
    assert is_kinefig_object("_KF_TMP_Cutter_001") is True
    assert is_kinefig_object("Cube") is False
    assert is_kinefig_object("Camera") is False
    assert is_kinefig_object("Light") is False
    assert is_kinefig_object("MyCharacter") is False


def test_is_temp_object():
    """Verify detection of temporary objects for cleanup."""
    assert is_temp_object("_KF_TMP_Cutter_001") is True
    assert is_temp_object("_KF_TMP_Helper") is True
    assert is_temp_object("KF_Joint_Ball_001") is False
    assert is_temp_object("Cube") is False


@pytest.mark.parametrize(
    "input_name, expected",
    [
        ("KF_Joint_Ball_001", "KF_Joint_Ball_001"),
        ("Part/Name with:illegal*chars?", "Part_Name_with_illegal_chars"),
        ("Arm L: Upper", "Arm_L_Upper"),
        ("  Dirty   Spaces  ", "Dirty_Spaces"),
    ],
)
def test_sanitize_filename(input_name, expected):
    """Verify filename sanitization produces valid filesystem names."""
    assert sanitize_filename(input_name) == expected
