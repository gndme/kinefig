# KineFig

KineFig is a commercial Blender add-on for building articulated, printable action figures faster.

> Working product name. Not yet a public release.

## V1 Focus

- Articulated humanoid figure workflows;
- Ball / double-ball joints;
- Peg/socket;
- Hinges;
- Split body parts;
- Placement and mirroring;
- Movement preview;
- Collision checks;
- Print clearance;
- Batch export.

## Architecture & Development Pipeline

```text
Product Owner / Antigravity
    ↓ Git push
GitHub Actions CI (Python 3.10-3.12 + Headless Blender 4.2.0 Linux)
    ↓ Unit tests (pytest) + real Blender runtime tests + extension validation
Tester Extension Artifact: kinefig-<version>-<pr_id>-<sha>.zip
    ↓
3D Specialist Workstation (Real Blender 4.2+)
    ↓ UAT Testing
In-Addon Help & Diagnostics (Copy Debug Info / Report Bug)
    ↓ Prefilled Issue Form
GitHub Issues (gndme/kinefig)
```

> [!NOTE]
> **Environment Model**: The Product Owner local machine codes and runs fast unit tests without requiring a local Blender installation. Real Blender runtime verification and extension validation are fully automated in CI on official Blender 4.2 runners. The 3D Specialist installs the CI-generated tester artifact for UAT.

## Quick Start for Developers

### Run Automated Unit Tests

```bash
python -m pytest -v
```

### Build Blender 4.2+ Extension Zip

```bash
python scripts/build_extension.py
```

Outputs deterministic extension package to `dist/kinefig-<version>.zip` and traceable tester artifact `dist/kinefig-<version>-<pr_id>-<sha>.zip`.

### Real Blender 4.2 Validation (CI or local if Blender installed)

```bash
# Validate extension package schema
blender --command extension validate dist/kinefig-0.0.1.zip

# Run headless runtime integration test on packaged zip artifact
blender --background --factory-startup --python tests/test_blender_runtime.py
```

## Status

**PR-002 Ball Joint Geometry Core (In Progress)**:
- Implements parametric male ball joint geometry with mm precision and exact watertight 2-manifold Boolean Union.
- Sidebar N-panel provides interactive controls for Ball Diameter, Stem Diameter, and Stem Length.
- *Known Limitation*: PR-002 provides the male ball joint core. The matching female socket engine will be introduced in PR-003.
