# Changelog

## 0.0.1 (PR-001 Foundation)
- Initial KineFig development scaffold.
- Centralized unit conversion (`mm_to_blender`, `blender_to_mm`) adhering to the Unit Contract (1 BU = 1 meter, all user dimensions in mm).
- Parameter validation primitives (`require_positive`, `require_non_negative`, `require_in_range`) with strict rejection of non-finite values (NaN, +inf, -inf).
- Deterministic sequential object naming allocator (`get_next_object_name`, `get_next_temp_name`) preventing collisions without relying on Blender auto-suffixes.
- 3D Viewport sidebar N-panel (`KineFig`) with visible version/build SHA badge and smoke test operator with Undo.
- Blender 4.2+ extension manifest (`blender_manifest.toml`).
- Deterministic, byte-for-byte reproducible build script (`scripts/build_extension.py`) producing both release package and traceable tester artifact (`kinefig-<version>-pr001-<sha>.zip`).
- Structured in-memory logging subsystem (`core/logging.py`) with bounded buffer and level support (INFO, WARNING, ERROR, DEBUG).
- Safe diagnostic data collector (`core/diagnostics.py`) and operators (`kinefig.copy_debug_info`, `kinefig.export_diagnostic_report`, `kinefig.report_bug`).
- GitHub Issue Form template (`.github/ISSUE_TEMPLATE/uat_bug.yml`) for streamlined 3D Specialist bug reporting without secrets.
- Comprehensive automated test suite:
  - 83 unit tests via pytest (units, validation, naming, manifest, packaging, lifecycle, logging, diagnostics, build_info).
  - Real Blender 4.2 headless runtime integration test (`tests/test_blender_runtime.py`).
- Official Blender 4.2 extension package validation (`blender --command extension validate`).
- GitHub Actions CI workflow for Python 3.10, 3.11, 3.12 with automated Blender 4.2 runner execution.
