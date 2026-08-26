# Changelog

## Unreleased (PR-003 Parametric Female Ball Socket Cavity Core)
- Parametric female Ball Socket cavity generator (`geometry/sockets.py`): creates watertight, closed 2-manifold cutter volume representing negative cavity space with mm precision.
- Centralized clearance mathematics (`core/clearance.py`): strictly enforces radial clearance contract (`socket_diameter = ball_diameter + 2 * clearance`).
- Parameter validation (`validate_ball_socket_parameters`): validates positive ball diameter, non-negative radial clearance, depth `< socket_diameter`, and strict integer tessellation.
- Operators `kinefig.create_ball_socket` and contextual `kinefig.use_selected_ball` (reads ball diameter directly from active KineFig ball joint).
- Hardened `use_selected_ball` operator against arbitrary/malformed metadata using `require_positive()`: safely rejects non-positive, non-finite (NaN, inf), string, or None metadata without crashing or mutating scene settings.
- Explicit insertion axis semantic contract: stores `kf_axis = (0, 0, 1)` (cavity axis), `kf_insertion_axis = (0, 0, 1)` (male travel direction into socket), and `kf_opening_normal = (0, 0, -1)` (outward normal of opening plane).
- UI integration in Sidebar N-panel: dedicated Ball Socket card with diameter, radial clearance, depth controls, computed cavity diameter readout, and one-click ball matching.
- Exact Boolean difference trimming: cleanly slices spherical cavity at insertion plane `z = 0` with flat capping polygon, ensuring 100% 2-manifold closed cutter volume.
- Guaranteed BMesh native resource lifecycle safety using `try / finally` blocks.
- Real Blender packaged zip integration tests (`tests/test_blender_runtime.py`): asserts 0 non-manifold edges, 0 boundary edges, positive volume, exact bounding box dimensions, axis metadata contract, malformed metadata rejection, and geometric clearance invariant (`cavity_radius - ball_radius == clearance`).
- *Note*: PR-003 generates socket cutter/cavity tool geometry; automatic Boolean subtraction into arbitrary body meshes belongs to future socket seating workflows.

## 0.0.2 (PR-002 Male Ball Joint Geometry Core)
- Parametric male Ball Joint generator (`geometry/joints.py`): creates watertight 2-manifold joint mesh (sphere + cylindrical stem) with mm precision.
- Exact Boolean Union construction eliminating internal overlapping faces for 3D printing readiness.
- Parameter validation (`validate_ball_joint_parameters`): enforces positive finite dimensions, `stem_diameter < ball_diameter`, and valid tessellation segments/rings.
- Operator `kinefig.create_ball_joint`: supports Undo, Redo panel, and 3D Cursor placement.
- Sidebar N-panel UI: interactive inputs for Ball Diameter, Stem Diameter, and Stem Length.
- Object naming & metadata: deterministic allocation (`KF_Joint_Ball_001`, `002`...) with parametric metadata (`kf_type="joint"`, `kf_joint_type="ball"`, dimensions, default axis +Z).
- Transactional geometry execution & rollback: introduced `KineFigGeometryError` and deterministic rollback of all allocated objects/meshes upon Boolean union or evaluation failure.
- Strict integer validation: added `require_integer_in_range()` strictly rejecting floats, booleans, strings, and non-finite values for segments and rings.
- Accurate temp prefix assertions: updated integration tests to assert zero orphan `_KF_TMP_` objects or mesh datablocks using `is_temp_object()` and `PREFIX_TEMP`.
- Factual metadata policy: eliminated uncomputed placeholder metadata (`kf_range_min`, `kf_range_max`, `kf_clearance_mm`, `kf_role`, `kf_side`) until respective engines exist.
- Real Blender packaged zip integration tests (`tests/test_blender_runtime.py`): asserts 100% 2-manifold edges, 0 boundary edges, positive volume, exact bounding box dimensions, unshielded Undo state transitions, and transactional rollback on failure.



## 0.0.1 (PR-001 Foundation)
- Initial KineFig development scaffold.
- Centralized unit conversion (`mm_to_blender`, `blender_to_mm`) adhering to the Unit Contract (1 BU = 1 meter, all user dimensions in mm).
- Parameter validation primitives (`require_positive`, `require_non_negative`, `require_in_range`) with strict rejection of non-finite values (NaN, +inf, -inf).
- Deterministic sequential object naming allocator (`get_next_object_name`, `get_next_temp_name`) preventing collisions without relying on Blender auto-suffixes.
- 3D Viewport sidebar N-panel (`KineFig`) with visible version/build SHA badge and smoke test operator with Undo.
- Blender 4.2+ extension manifest (`blender_manifest.toml`).
- Deterministic, byte-for-byte reproducible build script (`scripts/build_extension.py`) producing both release package and traceable tester artifact (`kinefig-<version>-<pr_id>-<sha>.zip`).
- Structured in-memory logging subsystem (`core/logging.py`) with bounded buffer and level support (INFO, WARNING, ERROR, DEBUG).
- Safe diagnostic data collector (`core/diagnostics.py`) and operators (`kinefig.copy_debug_info`, `kinefig.export_diagnostic_report`, `kinefig.report_bug`).
- GitHub Issue Form template (`.github/ISSUE_TEMPLATE/uat_bug.yml`) for streamlined 3D Specialist bug reporting without secrets.
- Comprehensive automated test suite:
  - 88 unit tests via pytest.
  - Real Blender 4.2 headless runtime integration test on packaged zip (`tests/test_blender_runtime.py`).
- Official Blender 4.2 extension package validation (`blender --command extension validate`).
- GitHub Actions CI workflow for Python 3.10, 3.11, 3.12 with automated Blender 4.2 runner execution.
