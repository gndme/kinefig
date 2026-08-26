"""Validation tests for blender_manifest.toml and bl_info consistency."""

from pathlib import Path
import toml
from addon.kinefig import bl_info

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "addon" / "kinefig" / "blender_manifest.toml"


def test_manifest_file_exists():
    """Verify that blender_manifest.toml exists."""
    assert MANIFEST_PATH.is_file(), f"Missing manifest at {MANIFEST_PATH}"


def test_manifest_toml_structure():
    """Verify manifest fields conform to Blender 4.2 extension specification."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = toml.load(f)

    required_keys = [
        "schema_version",
        "id",
        "version",
        "name",
        "tagline",
        "maintainer",
        "type",
        "blender_version_min",
        "license",
    ]
    for key in required_keys:
        assert key in data, f"Manifest missing required key: {key}"

    assert data["schema_version"] == "1.0.0"
    assert data["id"] == "kinefig"
    assert data["type"] == "add-on"
    assert data["blender_version_min"] == "4.2.0"
    assert isinstance(data["license"], list)
    assert any(lic.startswith("SPDX:") for lic in data["license"])


def test_version_consistency():
    """Verify that manifest version matches bl_info in __init__.py."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_data = toml.load(f)

    manifest_version = manifest_data["version"]
    bl_info_version = ".".join(str(n) for n in bl_info["version"])

    assert manifest_version == bl_info_version, (
        f"Version mismatch: manifest has '{manifest_version}' "
        f"while bl_info has '{bl_info_version}'"
    )
