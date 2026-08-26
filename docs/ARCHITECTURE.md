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

## Future Composition Model

Complex figure articulation should be composed from reusable primitives.

Example:

```text
SHF-style Double-Hinge Knee
=
split geometry
+ hinge primitive A
+ hinge primitive B
+ pin geometry
+ clearance rules
+ axis metadata
+ range metadata
+ optional aesthetic cover/seat
```

## Suggested Packages

```text
core/
  units.py
  validation.py
  context.py
  naming.py
  errors.py
  compatibility.py

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
