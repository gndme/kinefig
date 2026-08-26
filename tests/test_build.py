"""Tests for extension packaging and build reproducibility."""

import zipfile
import hashlib
from pathlib import Path
from scripts.build_extension import build_extension_zip, get_version, ROOT, DIST_DIR


def test_build_extension_produces_valid_zip(tmp_path):
    """Verify that build_extension_zip creates a valid zip containing required files."""
    test_zip = tmp_path / "kinefig_test.zip"
    build_extension_zip(test_zip, commit_sha="test123")

    assert test_zip.is_file()
    assert test_zip.stat().st_size > 0

    with zipfile.ZipFile(test_zip, "r") as zf:
        namelist = zf.namelist()

        # Root files required by Blender 4.2+ extension specification
        assert "blender_manifest.toml" in namelist
        assert "__init__.py" in namelist
        assert "core/__init__.py" in namelist
        assert "core/units.py" in namelist
        assert "core/validation.py" in namelist
        assert "core/naming.py" in namelist
        assert "core/build_info.py" in namelist
        assert "core/logging.py" in namelist
        assert "core/diagnostics.py" in namelist
        assert "operators/smoke.py" in namelist
        assert "operators/diagnostics.py" in namelist
        assert "ui/panel.py" in namelist

        # Verify build_info content injected
        build_info_content = zf.read("core/build_info.py").decode("utf-8")
        assert 'COMMIT_SHA = "test123"' in build_info_content

        # Verify excluded artifacts
        for name in namelist:
            assert "__pycache__" not in name, f"Found cache file in archive: {name}"
            assert not name.endswith(".pyc"), f"Found compiled bytecode in archive: {name}"
            assert not name.endswith(".pyo"), f"Found compiled bytecode in archive: {name}"
            assert ".git" not in name, f"Found git file in archive: {name}"
            assert ".DS_Store" not in name, f"Found DS_Store in archive: {name}"


def test_build_reproducibility(tmp_path):
    """Verify that multiple builds with identical parameters produce identical cryptographic hashes."""
    zip1 = tmp_path / "build1.zip"
    zip2 = tmp_path / "build2.zip"

    build_extension_zip(zip1, commit_sha="sha1234")
    build_extension_zip(zip2, commit_sha="sha1234")

    hash1 = hashlib.sha256(zip1.read_bytes()).hexdigest()
    hash2 = hashlib.sha256(zip2.read_bytes()).hexdigest()

    assert hash1 == hash2, "Builds are not reproducible: sha256 checksums differ"


def test_dist_build_target():
    """Verify the default dist output build."""
    version = get_version()
    expected_dist = DIST_DIR / f"kinefig-{version}.zip"
    build_extension_zip(expected_dist, commit_sha="857bfb1")

    assert expected_dist.is_file()
    assert expected_dist.stat().st_size > 0
