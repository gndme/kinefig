"""Build script for KineFig Blender Extension package.

Produces a reproducible zip archive conforming to Blender 4.2+ extension specifications:
- blender_manifest.toml at archive root
- all addon package files included
- __pycache__ and cache artifacts excluded
- deterministic file ordering and normalized file timestamps
"""

from pathlib import Path
import zipfile
import toml

ROOT = Path(__file__).resolve().parents[1]
ADDON_DIR = ROOT / "addon" / "kinefig"
DIST_DIR = ROOT / "dist"

# Fixed timestamp for reproducible zip builds (2026-01-01 00:00:00)
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)

EXCLUDE_PATTERNS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
}


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


def build_extension_zip(output_path: Path) -> Path:
    """Package the addon into a Blender 4.2+ extension zip."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    files_to_pack = []
    for path in ADDON_DIR.rglob("*"):
        if path.is_file() and not should_exclude(path):
            rel_path = path.relative_to(ADDON_DIR)
            files_to_pack.append((path, rel_path))

    # Sort files for deterministic archive order
    files_to_pack.sort(key=lambda item: str(item[1]))

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for src_path, arc_name in files_to_pack:
            # Normalize timestamp for reproducible build
            zinfo = zipfile.ZipInfo(str(arc_name.as_posix()), date_time=ZIP_TIMESTAMP)
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            zinfo.external_attr = 0o644 << 16  # standard file permissions
            with open(src_path, "rb") as f:
                zf.writestr(zinfo, f.read())

    return output_path


def main():
    version = get_version()
    out_file = DIST_DIR / f"kinefig-{version}.zip"
    build_extension_zip(out_file)
    print(f"Built extension package: {out_file} ({out_file.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
