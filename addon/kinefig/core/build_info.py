"""Build and version metadata for KineFig.

Updated during extension build packaging with the exact Git commit SHA
and release identifiers for traceability during 3D UAT.
"""

VERSION = "0.0.1"
COMMIT_SHA = "dev"
BUILD_DATE = "2026-08-26"
BUILD_ID = "dev"


def get_version_string() -> str:
    """Return a formatted version string for display in the UI."""
    short_sha = COMMIT_SHA[:7] if COMMIT_SHA != "dev" else "dev"
    return f"v{VERSION} (Build {short_sha})"


def get_short_sha() -> str:
    """Return the 7-character short commit SHA or 'dev'."""
    return COMMIT_SHA[:7] if COMMIT_SHA != "dev" else "dev"
