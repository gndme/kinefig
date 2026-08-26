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

## Development Workflow

Strict multi-role workflow defined in `AGENTS.md`:

```text
SPEC
→ IMPLEMENT
→ TEST
→ CHATGPT REVIEW
→ FIX
→ 3D UAT
→ RELEASE
```

## Quick Start for Developers

### Run Automated Unit Tests

```bash
python -m pytest -v
```

### Build Blender 4.2+ Extension Zip

```bash
python scripts/build_extension.py
```

Outputs deterministic extension package to `dist/kinefig-<version>.zip`.

### Run Official Blender 4.2 Extension Validation (if Blender installed)

```bash
blender --command extension validate dist/kinefig-0.0.1.zip
```

### Run Real Blender Runtime Integration Test (if Blender installed)

```bash
blender --background --factory-startup --python tests/test_blender_runtime.py
```

## Status

**PR-001 Foundation Completed.** Updated and ready for re-review.
