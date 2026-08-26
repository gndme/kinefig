"""Build script for KineFig Blender Extension package.

Produces a reproducible zip archive conforming to Blender 4.2+ extension specifications:
- blender_manifest.toml at archive root
- all addon package files included
- __pycache__ and cache artifacts excluded
- deterministic file ordering and normalized file timestamps
- injects Git commit SHA into core/build_info.py for UAT traceability
"""

import os
import subprocess
from pathlib import Path
import zipfile
import toml

ROOT = Path(__file__).resolve().parents[1]
ADDON_DIR = ROOT / "addon" / "kinefig"
DIST_DIR = ROOT / "dist"

# Fixed timestamp for reproducible zip builds (2026-01-01 00:00:00)
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def should_exclude(path: Path) -> bool:
    """Return True if path should be omitted from release package."""
    for part in path.parts:
        if part in ("__pycache__", ".pytest_cache", ".git"):
            return True
    if path.suffix in (".pyc", ".pyo"):
        return True
    if path.name == ".DS_Store":
        return True
    return False


def get_version() -> str:
    """Read version string from blender_manifest.toml."""
    manifest_path = ADDON_DIR / "blender_manifest.toml"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = toml.load(f)
    return data.get("version", "0.0.1")


def get_git_commit_sha() -> str:
    """Extract current git commit SHA or environment fallback."""
    env_sha = os.environ.get("GITHUB_SHA")
    if env_sha:
        return env_sha[:7]

    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "dev"


def generate_build_info_content(version: str, commit_sha: str) -> str:
    """Generate dynamic content for core/build_info.py."""
    return f'''"""Build and version metadata for KineFig.

Updated during extension build packaging with the exact Git commit SHA
and release identifiers for traceability during 3D UAT.
"""

VERSION = "{version}"
COMMIT_SHA = "{commit_sha}"
BUILD_DATE = "2026-08-26"
BUILD_ID = "pr001-{commit_sha}"


def get_version_string() -> str:
    """Return a formatted version string for display in the UI."""
    short_sha = COMMIT_SHA[:7] if COMMIT_SHA != "dev" else "dev"
    return f"v{{VERSION}} (Build {{short_sha}})"


def get_short_sha() -> str:
    """Return the 7-character short commit SHA or 'dev'."""
    return COMMIT_SHA[:7] if COMMIT_SHA != "dev" else "dev"
'''


def build_extension_zip(output_path: Path, commit_sha: str = "dev") -> Path:
    """Package the addon into a Blender 4.2+ extension zip with embedded build info."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    version = get_version()

    files_to_pack = []
    for path in ADDON_DIR.rglob("*"):
        if path.is_file() and not should_exclude(path):
            rel_path = path.relative_to(ADDON_DIR)
            files_to_pack.append((path, rel_path))

    # Sort files for deterministic archive order
    files_to_pack.sort(key=lambda item: str(item[1]))

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for src_path, arc_name in files_to_pack:
            zinfo = zipfile.ZipInfo(str(arc_name.as_posix()), date_time=ZIP_TIMESTAMP)
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            zinfo.external_attr = 0o644 << 16

            # If build_info.py, inject current commit SHA
            if arc_name.as_posix() == "core/build_info.py":
                content = generate_build_info_content(version, commit_sha).encode("utf-8")
                zf.writestr(zinfo, content)
            else:
                with open(src_path, "rb") as f:
                    zf.writestr(zinfo, f.read())

    return output_path


def main():
    version = get_version()
    commit_sha = get_git_commit_sha()

    # 1. Standard extension package
    standard_zip = DIST_DIR / f"kinefig-{version}.zip"
    build_extension_zip(standard_zip, commit_sha=commit_sha)
    print(f"Built extension package: {standard_zip} ({standard_zip.stat().st_size} bytes)")

    # 2. Traceable tester artifact for 3D Specialist UAT (Part B)
    tester_zip = DIST_DIR / f"kinefig-{version}-pr001-{commit_sha}.zip"
    build_extension_zip(tester_zip, commit_sha=commit_sha)
    print(f"Built tester artifact: {tester_zip} ({tester_zip.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
