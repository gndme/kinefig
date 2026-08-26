"""Tests for extension packaging and build reproducibility."""

import os
import zipfile
import hashlib
from pathlib import Path
from scripts.build_extension import (
    build_extension_zip,
    get_version,
    get_git_commit_sha,
    get_pr_build_identifier,
    ROOT,
    DIST_DIR,
)


def test_get_pr_build_identifier_dynamic(monkeypatch):
    """Verify PR identifier dynamically extracts pr numbers or feature slugs."""
    monkeypatch.setenv("GITHUB_HEAD_REF", "feature/pr-001-foundation")
    assert get_pr_build_identifier() == "pr001"

    monkeypatch.setenv("GITHUB_HEAD_REF", "feature/pr-002-units")
    assert get_pr_build_identifier() == "pr002"

    monkeypatch.setenv("GITHUB_HEAD_REF", "feature/ball-joint-core")
    assert get_pr_build_identifier() == "ball-joint-core"


def test_get_git_commit_sha_priority(monkeypatch):
    """Verify PR_HEAD_SHA is prioritized over GITHUB_SHA (which is merge commit in CI)."""
    monkeypatch.setenv("PR_HEAD_SHA", "fd6c47de20510f1b")
    monkeypatch.setenv("GITHUB_SHA", "c34cdc0mergecommit")
    assert get_git_commit_sha() == "fd6c47d"


def test_build_extension_produces_valid_zip(tmp_path):
    """Verify that build_extension_zip creates a valid zip containing required files."""
    test_zip = tmp_path / "kinefig_test.zip"
    build_extension_zip(test_zip, commit_sha="test123", build_id="pr001")

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
        assert "operators/joints.py" in namelist
        assert "operators/diagnostics.py" in namelist
        assert "geometry/__init__.py" in namelist
        assert "geometry/joints.py" in namelist
        assert "properties/__init__.py" in namelist
        assert "properties/joint_properties.py" in namelist
        assert "ui/panel.py" in namelist


        # Verify build_info content injected
        build_info_content = zf.read("core/build_info.py").decode("utf-8")
        assert 'COMMIT_SHA = "test123"' in build_info_content
        assert 'BUILD_ID = "pr001-test123"' in build_info_content

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

    build_extension_zip(zip1, commit_sha="sha1234", build_id="pr001", build_date="2026-08-26")
    build_extension_zip(zip2, commit_sha="sha1234", build_id="pr001", build_date="2026-08-26")

    hash1 = hashlib.sha256(zip1.read_bytes()).hexdigest()
    hash2 = hashlib.sha256(zip2.read_bytes()).hexdigest()

    assert hash1 == hash2, "Builds are not reproducible: sha256 checksums differ"


def test_dist_build_target():
    """Verify the default dist output build."""
    version = get_version()
    expected_dist = DIST_DIR / f"kinefig-{version}.zip"
    build_extension_zip(expected_dist, commit_sha="fd6c47d", build_id="pr001")

    assert expected_dist.is_file()
    assert expected_dist.stat().st_size > 0
