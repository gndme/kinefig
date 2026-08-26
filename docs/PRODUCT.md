# KineFig — Product Specification V1

## Working Name

**KineFig**

The name is a working commercial name and should receive a formal trademark/domain check before public launch.

## Category

Blender add-on for articulated action-figure design and 3D-print preparation.

## Initial Niche

Users who make SHF-style / highly articulated humanoid action figures, custom figures, garage kits, resin/FDM prototypes, and collectible figure parts.

KineFig is not affiliated with S.H.Figuarts, Bandai, or any other third-party brand.

## Product Promise

> Turn character meshes into articulated, printable figures faster.

## Core User

A user who already has or creates a character mesh in Blender, but does not want to manually repeat:
- splitting limbs;
- creating sockets;
- aligning joints;
- calculating clearance;
- rebuilding double joints;
- testing movement;
- exporting 15–30 separate parts.

## V1 Outcome

A user can take a prepared humanoid mesh and use KineFig to produce a basic articulated prototype with:
- head/neck articulation;
- shoulders;
- elbows;
- wrists;
- torso/waist;
- hips;
- knees;
- ankles;
- printable separated parts.

V1 does not promise one-click automatic conversion of any arbitrary character.

## V1 Modules

### 1. JOINT

#### Ball Joint
Parameters:
- ball diameter;
- stem diameter;
- stem length;
- socket clearance;
- socket depth.

#### Double Ball / Dumbbell Joint
Parameters:
- top ball diameter;
- bottom ball diameter;
- shaft diameter;
- shaft length;
- independent socket clearances.

Use cases:
- neck;
- wrist;
- torso;
- hip prototypes.

#### Peg + Socket
Parameters:
- peg diameter;
- peg length;
- insertion taper;
- socket clearance;
- socket depth.

#### Single Hinge
Parameters:
- pin diameter;
- hinge width;
- knuckle dimensions;
- travel range;
- clearance.

#### Double Hinge
Primary target:
- elbows;
- knees.

Must support:
- configurable spacing;
- two hinge axes;
- range preview.

#### Swivel
Primary target:
- bicep;
- thigh;
- waist;
- forearm.

#### Ankle Rocker
Combination joint for:
- dorsiflexion/plantarflexion;
- lateral rocker.

This is higher-risk than simple joints and may ship late in V1 if UAT finds geometry issues.

---

### 2. BODY

#### Split Limb
Split mesh by a controlled plane.

Primary targets:
- upper/lower arm;
- thigh/shin;
- wrist;
- ankle.

#### Split Torso
Controlled torso/waist separation.

#### Create Socket
Creates female receiver geometry against a selected target part.

#### Create Joint Seat
Creates supporting geometry around a joint where needed.

#### Mirror Joint
Mirrors joint placement and parameterization from L/R body regions.

#### Joint Placement Helper
V1 minimum:
- position;
- orientation;
- axis gizmo;
- numeric offsets;
- snap to selected surface/point.

V1 should not attempt fully automatic anatomical landmark detection.

---

### 3. TEST

#### Pose Preview
Temporary movement preview without committing destructive mesh changes.

#### Range Check
Displays intended angular range.

Example:

```text
Elbow
0° → 135°
```

#### Collision Check
Detects obvious mesh intersection during preview.

V1 collision checking can be conservative and does not need a physics simulation.

The goal is:
- warn;
- show problematic range;
- help user adjust geometry.

---

### 4. PRINT

#### Joint Clearance
Preset modes:

```text
Tight
Normal
Loose
Custom
```

V1 must let the user override numeric clearance.

Do not claim universal printer-specific accuracy.

#### Basic Part Check

Check:
- open/non-manifold mesh;
- inverted normals where detectable;
- invalid/zero geometry;
- obvious bad scale;
- missing expected part objects.

#### Batch STL Export

Export selected/registered figure parts with deterministic names.

Example:

```text
Head.stl
Torso_Upper.stl
Torso_Lower.stl
Arm_L_Upper.stl
Arm_L_Forearm.stl
...
```

---

## UX Structure

Sidebar:

```text
KINEFIG

JOINT
  Ball
  Double Ball
  Peg + Socket
  Hinge
  Double Hinge
  Swivel
  Ankle Rocker

BODY
  Split
  Socket
  Joint Seat
  Mirror
  Placement

TEST
  Pose Preview
  Range
  Collision

PRINT
  Clearance
  Part Check
  Batch Export
```

## UX Rule

A feature should remove meaningful repetitive Blender work.

Do not recreate trivial built-in actions.

## Non-Goals V1

- sculpting;
- retopology suite;
- UV;
- texturing;
- rendering;
- animation rigging;
- AI text-to-3D;
- automatic full-body segmentation;
- automatic anatomical landmark detection;
- automatic aesthetic correction;
- slicer replacement;
- supports/G-code.

## V1 Success Criteria

1. Clean install on supported Blender versions.
2. No scene-corrupting operations.
3. Reliable Undo for geometry tools.
4. Real 3D specialist can complete defined humanoid articulation UAT.
5. Joint presets produce usable starting geometry.
6. Batch export reliably names/separates parts.
7. First-time user can make at least one articulated joint workflow in under 10 minutes after installation.
8. Common joint workflow reduces manual Blender operations by at least 50%.

## Commercial Direction

V1 should launch as a paid local add-on.

Suggested ladder:

```text
Early Access: $19
V1 Standard:  $29
Mature V1.x:  $39 if feature quality justifies it
```

Major V2 may be a paid upgrade.

Avoid core subscriptions.

A future optional paid service may be justified only for recurring-cost functionality such as:
- cloud sync;
- hosted AI;
- team libraries;
- remote model analysis.

## Competitive Position

KineFig should not compete as a generic "3D printing joint addon."

Its differentiation should become:

> A figure-specific articulation workflow focused on humanoid action figures, joint aesthetics, movement range, symmetry, and printable part preparation.

