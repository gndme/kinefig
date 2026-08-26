"""Unit tests for core/build_info.py."""

from addon.kinefig.core.build_info import (
    VERSION,
    COMMIT_SHA,
    get_version_string,
    get_short_sha,
)


def test_build_info_constants():
    """Verify version and sha constants."""
    assert VERSION == "0.0.1"
    assert isinstance(COMMIT_SHA, str)


def test_get_version_string():
    """Verify formatted version string."""
    vs = get_version_string()
    assert vs.startswith("v0.0.1")


def test_get_short_sha():
    """Verify short sha returns 7 chars or 'dev'."""
    sha = get_short_sha()
    assert len(sha) <= 7
