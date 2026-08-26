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

### Run Automated Tests

```bash
python -m pytest -v
```

### Build Blender 4.2+ Extension Zip

```bash
python scripts/build_extension.py
```

Outputs deterministic extension package to `dist/kinefig-<version>.zip`.

## Status

**PR-001 Foundation Completed.** Ready for independent review.
