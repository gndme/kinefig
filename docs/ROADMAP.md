# KineFig — V1 Engineering Roadmap

## Phase 0 — Foundation

Deliver:
- add-on skeleton;
- Blender extension manifest;
- registration/unregistration;
- N-panel;
- centralized mm unit helpers;
- validation primitives;
- object naming;
- build script;
- smoke test;
- basic CI structure.

Exit gate:
- clean install;
- clean uninstall;
- create/remove a test object;
- Undo works;
- build ZIP is reproducible.

## Phase 1 — Joint Core

### 1. Ball Joint
Build:
- ball geometry;
- stem;
- socket;
- clearance;
- combined operator/UI.

### 2. Double Ball
Build on Ball Joint primitives.

### 3. Peg + Socket
Build:
- peg;
- optional taper;
- matching socket;
- clearance.

Exit gate:
- measured geometry correct;
- rotated/scaled target cases tested;
- basic UAT pass.

## Phase 2 — Split + Socket Engine

Build:
- split plane;
- safe mesh duplication/separation;
- joint side assignment;
- socket insertion into target;
- cleanup/Undo.

Exit gate:
- Split Limb UAT;
- Split Torso UAT;
- no unrelated mesh mutation.

## Phase 3 — Hinge System

Build:
- hinge base engine;
- pin;
- knuckles;
- axis metadata;
- clearance;
- single hinge;
- double hinge.

Primary UAT:
- elbow;
- knee.

## Phase 4 — Swivel + Ankle

Build:
- swivel;
- ankle rocker prototype.

Ankle rocker is allowed to move to V1.1 if it blocks V1 quality.

## Phase 5 — Placement + Symmetry

Build:
- placement gizmo;
- axis orientation;
- numeric offset;
- mirror joint;
- left/right metadata.

Primary UAT:
- shoulders;
- elbows;
- hips;
- knees.

## Phase 6 — Test System

Build:
- pose preview;
- angle control;
- nominal range;
- collision detection;
- collision warning display.

V1 collision check:
- no full physics;
- deterministic intersection checks are enough.

## Phase 7 — Print System

Build:
- clearance profile;
- custom clearance;
- part sanity checks;
- naming;
- batch STL export.

## Phase 8 — UAT Figure

Create a neutral internal humanoid test mesh or use a properly licensed test asset.

UAT matrix:
- neck;
- shoulders;
- elbows;
- wrists;
- waist;
- hips;
- knees;
- ankles.

Do not bundle copyrighted SHF/Bandai models.

## Phase 9 — V1 RC

Requirements:
- no BLOCKER/HIGH ChatGPT findings;
- core UAT pass;
- supported Blender versions pass;
- install docs;
- release notes;
- reproducible ZIP.

## PR Sequence

```text
PR-001 addon foundation
PR-002 units + validation
PR-003 ball joint geometry
PR-004 socket engine
PR-005 double-ball joint
PR-006 peg + socket
PR-007 split engine
PR-008 split limb UI
PR-009 hinge engine
PR-010 double hinge
PR-011 swivel
PR-012 placement
PR-013 mirror joint
PR-014 pose preview
PR-015 range check
PR-016 collision check
PR-017 clearance profiles
PR-018 part check
PR-019 batch export
PR-020 UAT fixes
PR-021 V1 RC
```
