# KineFig — 3D UAT Guide

## UAT Goal

Verify that KineFig produces workflows and joints that make sense to an experienced action-figure / Blender modeler.

The tester is evaluating product quality, not Python.

## Build Requirements Before UAT

A build may enter UAT only when:
- CI passes;
- ZIP installs;
- ChatGPT review has no BLOCKER/HIGH issues;
- developer smoke test passes.

## UAT Scoring

For each scenario:

```text
PASS
PASS WITH UX ISSUE
FAIL
BLOCKED
```

## Core Scenarios

### KF-UAT-JOINT-001 — Ball Joint

Goal:
Create a neck-style ball joint and matching socket.

Check:
- dimensions;
- placement;
- socket behavior;
- visible joint aesthetics;
- clearance control;
- Undo.

### KF-UAT-JOINT-002 — Double Ball

Goal:
Create a double-ball connector suitable for wrist/torso/neck experimentation.

Check:
- independent ball dimensions;
- shaft proportions;
- socket generation;
- movement practicality.

### KF-UAT-BODY-001 — Split Arm

Goal:
Split a continuous arm mesh into upper arm and forearm.

Check:
- predictable cut;
- normals;
- topology usability;
- no unrelated damage.

### KF-UAT-HINGE-001 — Elbow

Goal:
Create a printable elbow articulation.

Check:
- axis;
- bending range;
- collision;
- exposed-joint aesthetics;
- ability to hide/minimize joint visually.

### KF-UAT-HINGE-002 — Double-Hinge Knee

Goal:
Create a high-range knee prototype.

Check:
- hinge alignment;
- range;
- part count;
- collision;
- practical assembly.

### KF-UAT-MIRROR-001 — Symmetry

Goal:
Mirror a tested left-side joint to the right side.

Check:
- orientation;
- parameter parity;
- naming;
- no destructive transform surprises.

### KF-UAT-TEST-001 — Range Preview

Goal:
Preview a joint from minimum to maximum angle.

Check:
- intuitive control;
- correct pivot;
- collision feedback.

### KF-UAT-PRINT-001 — Export

Goal:
Export a multi-part figure setup.

Check:
- correct part list;
- deterministic file names;
- correct units/scale;
- no missing parts.

## Required Tester Feedback

For each feature:
1. Would you use this instead of manual Blender workflow?
2. Which clicks are unnecessary?
3. Which parameter names feel wrong?
4. Does the joint look acceptable on a collectible figure?
5. What would prevent this from being production-usable?
