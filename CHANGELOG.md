# Changelog

## 0.0.1 (PR-001 Foundation)
- Initial KineFig development scaffold.
- Centralized unit conversion (`mm_to_blender`, `blender_to_mm`).
- Parameter validation primitives (`require_positive`, `require_non_negative`, `require_in_range`).
- Standardized object and temporary naming conventions (`format_object_name`, `format_temp_name`).
- 3D Viewport sidebar N-panel (`KineFig`) and smoke test operator with Undo.
- Blender 4.2+ extension manifest (`blender_manifest.toml`).
- Deterministic, byte-for-byte reproducible build script (`scripts/build_extension.py`).
- Automated test suite (56 tests) covering units, validation, naming, manifest, lifecycle, and packaging.
- GitHub Actions CI workflow for Python 3.10, 3.11, 3.12.
