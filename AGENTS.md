# AGENTS.md — KineFig

## Purpose

KineFig is a commercial Blender add-on for articulated action-figure design, with SHF-style workflows as the initial niche.

Primary product promise:

> Turn character meshes into articulated, printable figures faster.

This repository uses a strict multi-role development workflow:

- **Product Owner:** defines product behavior, scope, acceptance criteria, pricing, and release decisions.
- **Antigravity:** implementation agent. It writes code only against approved specs.
- **ChatGPT:** independent reviewer. It reviews architecture, Blender API usage, runtime risks, geometry correctness, regression risk, tests, packaging, and release readiness.
- **3D Specialist:** domain/UAT expert. They validate real Blender workflows, articulation quality, topology usability, poseability, aesthetics, and print practicality. They are not expected to debug Python.

## Golden Workflow

```text
SPEC
→ ANTIGRAVITY IMPLEMENTS
→ AUTOMATED TESTS
→ CHATGPT REVIEW
→ ANTIGRAVITY FIXES
→ CHATGPT RE-REVIEW
→ BUILD ZIP
→ 3D UAT
→ FIX
→ RELEASE
```

Never send unfinished technical work to the 3D specialist.

---

## Product Rules

1. KineFig V1 is for articulated figures, not general CAD.
2. Do not duplicate Blender features unless KineFig removes substantial repetitive work.
3. Visible dimensions use millimeters.
4. Geometry generation must be deterministic.
5. User scenes must be protected.
6. Undo is mandatory for user-facing geometry operations where Blender supports it.
7. Invalid geometry must fail clearly instead of producing silent bad output.
8. Joint appearance matters as much as mechanical movement.
9. SHF-style articulation is a workflow reference, not a claim of affiliation with any third-party brand.
10. Never bundle copyrighted third-party character meshes or proprietary figure parts.

---

## Feature Contract

Antigravity must not implement a feature without a contract.

Each feature requires:

```text
FEATURE
USER GOAL
SUPPORTED CONTEXT
INPUT
OUTPUT
BEHAVIOR
PARAMETERS
VALIDATION
ERROR STATES
UNDO
DESTRUCTIVE / NON-DESTRUCTIVE POLICY
AUTOMATED TESTS
UAT SCENARIOS
KNOWN LIMITATIONS
```

If behavior is ambiguous, return:

```text
NEEDS_PRODUCT_DECISION
```

Do not invent product behavior.

---

## Architecture

```text
UI
↓
Operator
↓
Tool / Domain Service
↓
Geometry Engine
↓
Blender API
```

Keep operators thin. Do not place geometry algorithms in Panel.draw() or large execute() methods.

Recommended structure:

```text
addon/kinefig/
├── __init__.py
├── blender_manifest.toml
├── core/
├── geometry/
├── operators/
├── properties/
├── ui/
└── presets/
```

### Core

Owns:
- units;
- validation;
- context guards;
- naming;
- common result/error types;
- compatibility helpers.

### Geometry

Owns:
- primitives;
- booleans;
- sockets;
- pegs;
- hinge geometry;
- split operations;
- clearance offsets;
- collision helper geometry.

### Operators

Translate Blender context into explicit validated parameters.

### UI

Presents user intent:
- JOINT
- BODY
- TEST
- PRINT

Avoid exposing internal Blender implementation concepts unless needed.

---

## Blender API Rules

Prefer explicit data APIs and `bmesh` when practical.

Use `bpy.ops` only when operator/context behavior is appropriate and controlled.

Every context-sensitive operation must consider:
- active object;
- selected objects;
- current mode;
- transforms;
- collection;
- hidden state;
- headless/background execution.

Never assume:
- Object Mode;
- zero rotation;
- applied scale;
- world origin;
- a default cube;
- exactly one selected object.

---

## Scene Safety

Never silently:
- delete unrelated objects;
- apply unrelated modifiers;
- rename unrelated objects;
- change scene units;
- alter user preferences;
- leave orphan cutters;
- modify another add-on;
- flatten user geometry without explicit action.

Temporary objects must use a KineFig prefix and be cleaned deterministically.

Generated objects use names such as:

```text
KF_Joint_Ball_001
KF_Joint_DoubleBall_001
KF_Socket_001
KF_SplitPlane_001
KF_FigurePart_L_UpperArm
```

---

## Units

All user-facing dimensions are millimeters.

Centralize conversion in:

```text
core/units.py
```

Do not scatter raw `/1000` conversions across feature code.

---

## Joint Semantics

Every joint feature must define:

- male geometry;
- female geometry;
- articulation axis/axes;
- clearance model;
- insertion direction;
- nominal range of motion;
- collision assumptions;
- print assumptions;
- minimum viable wall thickness constraints where applicable.

Joint generation must not be treated as decorative mesh creation.

---

## V1 Scope

### JOINT

- Ball Joint
- Double Ball / Dumbbell Joint
- Peg + Socket
- Single Hinge
- Double Hinge
- Swivel
- Ankle Rocker

### BODY

- Split Limb
- Split Torso
- Create Socket
- Create Joint Seat
- Mirror Joint
- Joint Placement helpers

### TEST

- Pose Preview
- Range Check
- Collision Check

### PRINT

- Joint Clearance
- Basic Part Check
- Batch STL Export

Anything outside V1 requires Product Owner approval.

---

## Definition of Done — Antigravity

Before requesting ChatGPT review:

```text
[ ] feature spec implemented
[ ] addon registers
[ ] addon unregisters
[ ] normal workflow has no console exception
[ ] unit conversion verified
[ ] validation implemented
[ ] Undo verified
[ ] Redo checked where relevant
[ ] temporary objects cleaned
[ ] unrelated scene state preserved
[ ] automated tests added
[ ] tests pass
[ ] build ZIP succeeds
[ ] documentation updated
```

Allowed status values:

```text
DONE
BLOCKED
PARTIAL
NEEDS_PRODUCT_DECISION
```

Antigravity must not say DONE for unverified work.

---

## ChatGPT Review Contract

Review priorities:

1. scene/data corruption;
2. Blender runtime/API correctness;
3. geometry correctness;
4. joint mechanics;
5. Undo/cleanup;
6. unit correctness;
7. architecture;
8. regression risk;
9. performance;
10. UX consistency;
11. maintainability.

Severity:

```text
BLOCKER
HIGH
MEDIUM
LOW
NIT
```

No feature may enter 3D UAT with unresolved BLOCKER or HIGH findings.

Review request must include:

```text
REPO
BASE
HEAD
FEATURE SPEC
TARGET BLENDER VERSION
KNOWN LIMITATIONS
REQUEST TYPE
```

---

## Fix Protocol

After review, Antigravity must answer every finding with:

```text
FIXED
NOT_REPRODUCIBLE + evidence
ACCEPTED_RISK + Product Owner approval
```

Then run the relevant complete test set and request re-review.

---

## Automated Test Matrix

Use unit tests for:
- unit conversion;
- validation;
- clearance math;
- naming;
- joint parameter relationships.

Use Blender integration tests for:
- registration;
- object creation;
- split behavior;
- transforms;
- expected object counts;
- cleanup;
- dimensions;
- modifier/state preservation.

Where applicable test:
- default object;
- translated object;
- rotated object;
- non-uniform scale;
- existing modifiers;
- multiple objects;
- wrong selection;
- wrong mode;
- invalid dimensions;
- tiny valid values;
- repeated operation;
- Undo.

Geometry assertions should prefer measurable facts:
- dimensions;
- bounding boxes;
- manifold state;
- normals;
- expected parts;
- socket/peg relationships.

Do not rely only on screenshots.

---

## 3D Specialist UAT

3D UAT begins only after:

```text
CI PASS
+
BUILD PASS
+
CHATGPT REVIEW: no BLOCKER/HIGH
+
DEV ACCEPTANCE PASS
```

The specialist validates:
- workflow naturalness;
- placement;
- joint aesthetics;
- silhouette preservation;
- movement range;
- collisions;
- topology usability;
- print practicality;
- terminology;
- click reduction.

They are not responsible for Python debugging.

UAT issue template:

```text
ID
BUILD
BLENDER VERSION
OS
SEVERITY
STARTING STATE
STEPS
EXPECTED
ACTUAL
EVIDENCE
```

---

## Branch Strategy

```text
main
develop
feature/<feature-name>
fix/<issue>
release/<version>
```

Keep PRs small and single-purpose.

Preferred early sequence:

```text
01 addon skeleton
02 units + validation
03 ball joint
04 socket engine
05 double ball
06 peg + socket
07 split engine
08 hinge
09 double hinge
10 swivel
11 ankle rocker
12 joint placement
13 mirror joint
14 pose preview
15 range check
16 collision check
17 clearance system
18 batch export
19 UX polish
20 V1 RC
```

---

## Release Gate

```text
[ ] manifest valid
[ ] clean ZIP install works
[ ] clean Blender profile test works
[ ] register/unregister passes
[ ] smoke tests pass
[ ] supported Blender versions tested
[ ] no BLOCKER/HIGH findings
[ ] required UAT scenarios pass
[ ] README updated
[ ] CHANGELOG updated
[ ] version updated
[ ] reproducible release ZIP generated
```

---

## Commercial / Licensing Rule

The Blender add-on must use GPL-compatible distribution terms where required by Blender's Python API ecosystem.

Do not build the business model around hiding distributed Python source.

Commercial value should come from:
- official builds;
- updates;
- support;
- documentation;
- polished UX;
- tested joint presets;
- workflow quality;
- optional external services later.

V1 is local-first and must not require network access.

---

## Decision Authority

- Product behavior: Product Owner.
- Real figure workflow usability: 3D Specialist feedback + Product Owner decision.
- Technical correctness: evidence/tests.
- Architecture: ChatGPT recommends; Product Owner approves significant changes.
- Implementation details: Antigravity, within approved architecture/spec.

---

## Canonical Git Repository

The canonical repository for this project is:

```text
https://github.com/gndme/kinefig
```

Repository identifier:

```text
gndme/kinefig
```

Antigravity must treat this repository as the single source of truth for KineFig.

### Git Delivery Rules

For every implementation task:

1. Work against `gndme/kinefig`.
2. Pull/fetch the latest target branch before starting.
3. Create or use the approved branch according to the branch strategy in this file.
4. Implement only the approved feature scope.
5. Run the required tests and build checks.
6. Commit all completed work with meaningful commit messages.
7. Push the branch to:

```text
origin = https://github.com/gndme/kinefig
```

8. Report the exact pushed branch name, commit SHA, base branch, and test/build result.
9. Do not leave completed source changes only on the local machine.
10. Do not force-push `main` or rewrite published history unless the Product Owner explicitly requests it.
11. Do not merge release-bound work into `main` before the required ChatGPT review and UAT gates have passed.
12. If Git authentication, permissions, conflicts, or remote state prevent a push, return `BLOCKED` with the exact error instead of claiming the task is complete.

A task that changes source code is **not DONE** until the corresponding approved changes have been committed and pushed to `gndme/kinefig`.

### Required Completion Report

For any source-code implementation, Antigravity's completion message must contain:

```text
STATUS: DONE | BLOCKED | PARTIAL | NEEDS_PRODUCT_DECISION
REPO: gndme/kinefig
BRANCH: <branch>
BASE: <base branch/commit>
HEAD: <commit SHA>
PUSHED: YES | NO
TESTS: <summary>
BUILD: PASS | FAIL | NOT_APPLICABLE
NEXT: <recommended next review/action>
```

When `PUSHED: NO`, status cannot be `DONE` for a source-code task.

## Final Rule

The product is not a collection of random joint generators.

KineFig must steadily evolve toward:

```text
Character Mesh
→ Split
→ Place Joint
→ Generate Mechanical Geometry
→ Preview Articulation
→ Detect Collision
→ Apply Clearance
→ Export Printable Parts
```
