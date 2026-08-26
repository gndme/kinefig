# KineFig — V1 Engineering Roadmap

## Phase 0 — Foundation & Infrastructure

### PR-001 — Foundation, Units, Validation & Diagnostics (COMPLETED)
Delivered:
- Add-on skeleton & Blender 4.2+ extension manifest;
- Centralized mm Unit Contract (`1 BU = 1m`, UI in mm, raw geometry conversion);
- Parameter validation engine (rejecting 0, negative, NaN, inf);
- Deterministic naming allocator (`KF_Smoke_Ball_001`, `KF_Smoke_Ball_002`...);
- In-memory structured logging subsystem with bounded buffer;
- Safe diagnostic metadata collector & UAT bug reporting flow (`.github/ISSUE_TEMPLATE/uat_bug.yml`);
- Reproducible extension build pipeline producing standard package and traceable tester artifact;
- Comprehensive automated unit tests & real Blender 4.2 packaged zip runtime integration tests in CI.

Exit gate: **PASSED (Merged into main)**.

---

## Phase 1 — Joint Geometry Core

### PR-002 — Ball Joint Geometry Core (COMPLETED)
Delivered:
- Parametric male ball joint geometry (sphere + cylindrical stem);
- Watertight 2-manifold mesh construction via Exact Boolean Union;
- Dedicated Joint UI panel in 3D Viewport sidebar;
- Joint metadata schema (`kf_type="joint"`, `kf_joint_type="ball"`, dimensions, axis);
- Deterministic sequential naming (`KF_Joint_Ball_001`, `KF_Joint_Ball_002`...);
- Undo support and transactional rollback on Boolean failure;
- Real Blender packaged zip integration tests for geometry dimensions, manifoldness, and Undo.

Exit gate: **PASSED (Merged into main)**.

### PR-003 — Socket Engine Core (COMPLETED)
Delivered:
- Parametric female socket cavity generator for ball joints;
- Radial clearance offset contract (`socket_diameter = ball_diameter + 2 * clearance`);
- Watertight, closed 2-manifold cutter volume trimmed cleanly at insertion plane `z = 0`;
- Depth semantics: distance from opening plane to deepest cavity point (`0 < depth < diameter`);
- Contextual UX operator `kinefig.use_selected_ball` to copy diameter from active male joint;
- Transactional rollback on Boolean failure and factual metadata schema;
- Real Blender packaged zip integration tests for dimensions, manifoldness, and clearance invariant.

Exit gate: **PASSED (Merged into main)**.

### PR-004 — Double Ball Joint (Dumbbell) (UNDER 3D UAT)
Build on Ball Joint and Socket primitives:
- Independent dual ball dimensions;
- Center connecting shaft;
- Wrist, neck, and torso articulation presets.

### PR-005 — Peg + Socket Core (IMPLEMENTED)
Delivered:
- Parametric male cylindrical peg with optional draft/taper angle;
- Matching female receiver socket cutter volume;
- Direct BMesh closed watertight 2-manifold geometry (no Booleans required);
- Explicit radial clearance model (`socket_diameter = peg_diameter + 2 * radial_clearance`);
- Contextual UX operator `kinefig.use_selected_peg` to match socket settings from active peg;
- Transactional rollback on failure, full Undo support, and factual metadata schema;
- Unit test suite (231 tests) and real Blender 4.2 packaged zip runtime integration tests.

Exit gate:
- Measured geometry correct;
- Clearance invariant verified;
- Real Blender packaged zip tests pass.

---

## Phase 2 — Split + Socket Engine

### PR-006 — Split Engine
Build:
- Split plane generation;
- Safe mesh separation;
- Boundary capping and normal preservation.

### PR-007 — Split Limb & Torso UI
Build:
- Split limb workflow operator;
- Part naming (`KF_FigurePart_...`);
- Clean Undo and modifier preservation.

---

## Phase 3 — Hinge System

### PR-008 — Single Hinge Engine
Build:
- Hinge base geometry, pin, knuckles;
- Articulation axis metadata;
- Elbow / knee articulation prototype.

### PR-009 — Double Hinge
Build:
- High-range double-pivot knee/elbow articulation;
- Center block geometry;
- Part count and collision check.

---

## Phase 4 — Swivel & Ankle Rocker

### PR-010 — Swivel Articulation
Build:
- Axial swivel rotation joint (bicep, thigh);
- Retention rim and peg.

### PR-011 — Ankle Rocker
Build:
- Dual-axis ankle articulation prototype.

---

## Phase 5 — Placement & Symmetry

### PR-012 — Placement Helpers
Build:
- 3D Cursor and landmark alignment;
- Joint orientation alignment gizmo.

### PR-013 — Mirror Joint
Build:
- Left-to-right joint symmetry mirroring;
- Name updating (`_L_` to `_R_`);
- Parity preservation.

---

## Phase 6 — Articulation Test System

### PR-014 — Pose Preview
### PR-015 — Range Check
### PR-016 — Collision Detection

---

## Phase 7 — 3D Print Preparation

### PR-017 — Clearance Profiles
### PR-018 — Part Sanity Check
### PR-019 — Batch STL Export

---

## Phase 8 & 9 — UAT Figure & V1 RC

### PR-020 — 3D Specialist UAT Polish
### PR-021 — V1 Release Candidate

---

## PR Sequence Summary

```text
PR-001 addon foundation + units + validation + diagnostics + packaging [DONE]
PR-002 ball joint geometry core [IN PROGRESS]
PR-003 socket engine
PR-004 double ball joint
PR-005 peg + socket
PR-006 split engine
PR-007 split limb UI
PR-008 single hinge
PR-009 double hinge
PR-010 swivel
PR-011 ankle rocker
PR-012 placement helpers
PR-013 mirror joint
PR-014 pose preview
PR-015 range check
PR-016 collision check
PR-017 clearance profiles
PR-018 part check
PR-019 batch export
PR-020 UAT polish
PR-021 V1 RC
```
