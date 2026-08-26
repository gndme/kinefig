# KineFig — Architecture

## Design Goal

Support increasingly complex articulated-figure workflows without turning each joint into a one-off script.

## Layer Model

```text
UI
→ Operators
→ Domain Tools
→ Geometry Primitives
→ Blender Data/BMesh APIs
```

## Unit Contract

1. **Internal Representation**:
   - KineFig geometry internally uses Blender standard coordinates where:
     `1 Blender Unit (BU) = 1 meter`.
   - All mesh vertex positions, primitive radii, and distances are computed using:
     `blender_coord = mm_value / 1000.0` (centralized in `core.units.mm_to_blender`).

2. **User Interface**:
   - All user-facing dimensions, inputs, and readout panels are strictly in **millimeters (mm)**.

3. **Scene Protection**:
   - KineFig must **NOT** alter user scene unit settings (`scene.unit_settings.system`, `scene.unit_settings.scale_length`, or `scene.unit_settings.length_unit`).
   - Geometry calculations are pure and do not depend on the user's display unit settings.
   - If a user changes scene unit scale, mesh vertex coordinates remain internally consistent in raw Blender metric units.

4. **STL & Export Workflow (V1 Roadmap)**:
   - When exporting for 3D printing (slicers that assume 1 unit = 1 mm), the exporter will apply the necessary scaling factor (1000x) so that a 10 mm figure joint exports as exactly 10 mm in the slicer.

## Joint Geometry Policy & Ball Joint Core (PR-002)

### Manifold Union vs Overlapping Meshes
- **Policy Choice**: KineFig uses **Exact Boolean Union** for articulated figure joints.
- Rather than leaving overlapping, self-intersecting mesh shells inside a single datablock, the geometry engine applies Blender's `EXACT` boolean union solver to dissolve internal geometry and weld the intersection seam into a continuous, watertight 2-manifold surface.
- **Benefits**:
  - Direct 3D print readiness across all slicers (Cura, PrusaSlicer, Bambu Studio) without non-manifold or self-intersection warnings;
  - Clean foundation for future socket subtraction, chamfers, and clearances without internal face artifacts.

### Transforms & Coordinate Conventions
- **Creation Location**: Default is the active 3D Cursor location (`context.scene.cursor.location`).
- **Orientation**: Default local joint axis points along **+Z** (from the stem base towards the spherical ball center).
- **Local Origin**: `(0, 0, 0)` is positioned at the base of the stem.
- **Stem Cylinder**: Extends from `z = 0` to `z = stem_length_m`.
- **Ball Sphere**: Centered at `(0, 0, stem_length_m)` with radius `ball_diameter_m / 2.0`.
- **Total Height**: `stem_length_m + ball_radius_m`.

### Parametric Metadata Schema
Every generated joint carries only factual properties validated and computed at creation time:
- `kf_type`: `"joint"`
- `kf_joint_type`: `"ball"`
- `kf_version`: KineFig version string
- `kf_ball_diameter_mm`: Ball diameter in mm (float)
- `kf_stem_diameter_mm`: Stem diameter in mm (float)
- `kf_stem_length_mm`: Stem length in mm (float)
- `kf_axis`: Articulation/orientation axis (default `(0.0, 0.0, 1.0)`)
*Policy*: Uncomputed properties (e.g. `kf_range_min`, `kf_range_max`, `kf_clearance_mm`, `kf_role`, `kf_side`) are strictly omitted until their respective engines are implemented.

### Transactional Geometry Policy
- Geometry operations must be transactional.
- If Boolean union, depsgraph evaluation, or postcondition checks fail:
  - All allocated temporary and target objects, meshes, and modifiers are immediately and deterministically removed (`do_unlink=True`);
  - Unrelated scene state is preserved untouched;
  - A descriptive `KineFigGeometryError` is raised;
  - The operator catches the error, logs it, and returns `{"CANCELLED"}` with a user-facing error report.


## Diagnostic & Bug Reporting Architecture


### Security Rule
- **NO embedded tokens or secrets**: KineFig never embeds GitHub Personal Access Tokens, OAuth secrets, or write credentials in client add-on code.
- **Privacy First**: Diagnostic collection only extracts safe system metadata (version, build SHA, Blender version, OS platform, unit settings, recent operational logs).
- Never automatically collects or uploads: `.blend` files, mesh vertex coordinates, textures, character names, or arbitrary filesystem paths.

### Two-Tier Submission Architecture
- **Mode 1 (V1 Foundation - Active)**:
  - Generates prefilled GitHub Issue URLs targeting `.github/ISSUE_TEMPLATE/uat_bug.yml`.
  - The tester authenticates directly on GitHub to submit.
- **Mode 2 (Future Remote API - Extensible Interface)**:
  - Defines `BugReportSenderInterface` in `core/diagnostics.py`.
  - Future implementation forwards reports to an authenticated KineFig backend proxy that manages GitHub API credentials securely server-side.

## Structured Logging Architecture
- Centralized in `core/logging.py`.
- In-memory bounded circular buffer (`deque(maxlen=100)`) preventing memory leaks during long modeling sessions.
- Captures operational milestones: operator start, validated inputs, generated object IDs, cleanup, and caught exceptions.

## Suggested Packages

```text
core/
  units.py
  validation.py
  naming.py
  build_info.py
  logging.py
  diagnostics.py
  errors.py
  context.py

geometry/
  primitives.py
  boolean.py
  sockets.py
  pegs.py
  hinges.py
  splits.py
  offsets.py
  collision.py

operators/
  smoke.py
  diagnostics.py
  joints.py
  body.py
  test.py
  print.py

properties/
  joint_properties.py
  scene_properties.py

ui/
  panel.py
  joint_panel.py
  body_panel.py
  test_panel.py
  print_panel.py

presets/
  clearance.py
  joints.py
```

## Parametric Metadata

Every KineFig-generated joint should carry metadata when practical:

```text
kf_type
kf_version
kf_joint_type
kf_axis
kf_range_min
kf_range_max
kf_clearance
kf_role
kf_side
```

This allows later tools to understand existing KineFig geometry.

## V2 Readiness

V1 architecture must not block:
- joint templates;
- anatomical presets;
- feature tree;
- natural-language parameter creation;
- automatic landmark assistance;
- procedural regeneration.

Do not implement these prematurely.
