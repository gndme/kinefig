"""Build script for KineFig Blender Extension package.

Produces a reproducible zip archive conforming to Blender 4.2+ extension specifications:
- blender_manifest.toml at archive root
- all addon package files included
- __pycache__ and cache artifacts excluded
- deterministic file ordering and normalized file timestamps
- injects Git commit SHA, dynamic build date, and dynamic PR ID into core/build_info.py for UAT traceability
"""

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import zipfile
import toml

ROOT = Path(__file__).resolve().parents[1]
ADDON_DIR = ROOT / "addon" / "kinefig"
DIST_DIR = ROOT / "dist"

# Fixed timestamp for reproducible zip archive entries (2026-01-01 00:00:00)
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
    """Extract current git commit SHA.

    Prioritizes PR_HEAD_SHA (the real PR branch HEAD) over GITHUB_SHA
    (which GitHub Actions sets to the merge-ref commit).
    """
    # 1. Explicit PR head SHA passed from CI
    pr_head_sha = os.environ.get("PR_HEAD_SHA")
    if pr_head_sha:
        return pr_head_sha[:7]

    # 2. Local git repository query
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
        pass

    # 3. Fallback to GITHUB_SHA if present
    env_sha = os.environ.get("GITHUB_SHA")
    if env_sha:
        return env_sha[:7]

    return "dev"


def get_pr_build_identifier() -> str:
    """Dynamically determine PR or branch identifier without hardcoding.

    Extracts 'pr001', 'pr002' from branch names like 'feature/pr-001-foundation'.
    """
    # Check environment variables
    ref = (
        os.environ.get("BUILD_ID")
        or os.environ.get("GITHUB_HEAD_REF")
        or os.environ.get("GITHUB_REF_NAME")
    )
    if not ref:
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            ref = res.stdout.strip()
        except Exception:
            ref = "dev"

    match = re.search(r"pr-?(\d+)", ref, re.IGNORECASE)
    if match:
        return f"pr{int(match.group(1)):03d}"

    if ref.startswith("feature/"):
        return ref.replace("feature/", "").replace("/", "-")

    return "dev"


def get_build_date() -> str:
    """Return ISO date string for build."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def generate_build_info_content(version: str, commit_sha: str, build_id: str, build_date: str) -> str:
    """Generate dynamic content for core/build_info.py."""
    return f'''"""Build and version metadata for KineFig.

Updated during extension build packaging with the exact Git commit SHA
and release identifiers for traceability during 3D UAT.
"""

VERSION = "{version}"
COMMIT_SHA = "{commit_sha}"
BUILD_DATE = "{build_date}"
BUILD_ID = "{build_id}-{commit_sha}"


def get_version_string() -> str:
    """Return a formatted version string for display in the UI."""
    short_sha = COMMIT_SHA[:7] if COMMIT_SHA != "dev" else "dev"
    return f"v{{VERSION}} (Build {{short_sha}})"


def get_short_sha() -> str:
    """Return the 7-character short commit SHA or 'dev'."""
    return COMMIT_SHA[:7] if COMMIT_SHA != "dev" else "dev"
'''


def build_extension_zip(output_path: Path, commit_sha: str = "dev", build_id: str = "dev", build_date: str = "") -> Path:
    """Package the addon into a Blender 4.2+ extension zip with embedded build info."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    version = get_version()
    b_date = build_date or get_build_date()

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

            # If build_info.py, inject current commit SHA, build date, and dynamic build ID
            if arc_name.as_posix() == "core/build_info.py":
                content = generate_build_info_content(version, commit_sha, build_id, b_date).encode("utf-8")
                zf.writestr(zinfo, content)
            else:
                with open(src_path, "rb") as f:
                    zf.writestr(zinfo, f.read())

    return output_path


def main():
    version = get_version()
    commit_sha = get_git_commit_sha()
    build_id = get_pr_build_identifier()
    build_date = get_build_date()

    # 1. Standard extension package
    standard_zip = DIST_DIR / f"kinefig-{version}.zip"
    build_extension_zip(standard_zip, commit_sha=commit_sha, build_id=build_id, build_date=build_date)
    print(f"Built extension package: {standard_zip} ({standard_zip.stat().st_size} bytes)")

    # 2. Traceable tester artifact for 3D Specialist UAT (dynamically named)
    tester_zip = DIST_DIR / f"kinefig-{version}-{build_id}-{commit_sha}.zip"
    build_extension_zip(tester_zip, commit_sha=commit_sha, build_id=build_id, build_date=build_date)
    print(f"Built tester artifact: {tester_zip} ({tester_zip.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
