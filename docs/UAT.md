# KineFig — 3D UAT Guide

## UAT Goal

Verify that KineFig produces workflows and joints that make sense to an experienced action-figure / Blender modeler.

The tester is evaluating product quality, articulation, and ergonomics, not debugging Python code.

---

## Environment & Development Pipeline

```text
Product Owner / Antigravity
    ↓ Git push (feature branch)
GitHub Actions CI (Python 3.10-3.12 + Headless Blender 4.2.0 Linux)
    ↓ Automated unit tests + real Blender runtime tests + extension validation
CI Tester Build Artifact: kinefig-<version>-pr001-<sha>.zip
    ↓ Download by 3D Specialist
3D Specialist Workstation (Real Blender 4.2+)
    ↓ UAT Testing
In-Addon Help & Diagnostics (Copy Debug Info / Report Bug)
    ↓ Prefilled Issue URL
GitHub Issues (gndme/kinefig)
```

> [!NOTE]
> **Environment Constraint**: The Product Owner local machine does **not** have Blender installed and is not required to install Blender. All real Blender runtime verification runs automatically in headless CI. The 3D Specialist installs the CI-built tester artifact on their own Blender installation for testing.

---

## Build Requirements Before UAT

A build may enter UAT only when:
- CI passes (unit tests + real Blender runtime integration test);
- Extension validation passes (`blender --command extension validate`);
- ChatGPT review has no BLOCKER or HIGH issues;
- Traceable tester ZIP artifact is generated (`kinefig-<version>-pr001-<sha>.zip`).

---

## In-Addon Diagnostics & Bug Reporting

When encountering an issue, visual flaw, or unexpected behavior during UAT:

1. In the 3D Viewport, open the **KineFig** sidebar panel.
2. Verify the version and commit SHA shown in the header (e.g. `v0.0.1 (Build 857bfb1)`).
3. Under **Help & Diagnostics**:
   - **Copy Debug Info**: Copies safe non-sensitive environmental data to your clipboard.
   - **Export Diagnostic Report**: Saves `report.json`, `kinefig.log`, and `system.txt` for offline sharing.
   - **Report Bug on GitHub**: Opens your browser directly to the GitHub Issue Form with environment diagnostics prefilled.

> [!IMPORTANT]
> **Privacy Guarantee**: KineFig diagnostic reports never automatically include `.blend` files, mesh coordinates, textures, character names, or private model data.

---

## UAT Scoring

For each scenario:

```text
PASS
PASS WITH UX ISSUE
FAIL
BLOCKED
```

---

## Core Scenarios

### KF-UAT-FOUNDATION-001 — Add-on Skeleton & Diagnostics (PR-001)

Goal:
Install the tester ZIP, verify UI panel, execute test sphere, test repeated execution, and test diagnostic reporting.

Check:
- Extension installs cleanly via Preferences > Add-ons (or Extensions in 4.2+);
- KineFig tab appears in 3D Viewport sidebar;
- Header displays exact version and build short SHA matching the downloaded ZIP;
- "Create Test Ball (10mm)" generates `KF_Smoke_Ball_001` with 10mm diameter;
- Repeated clicking generates `KF_Smoke_Ball_002` without collision or overwrite;
- "Copy Debug Info" copies valid text to clipboard;
- "Report Bug on GitHub" opens prefilled issue template;
- Undo removes generated sphere.

---

### KF-UAT-JOINT-001 — Ball Joint
Goal: Create a neck-style ball joint and matching socket.

### KF-UAT-JOINT-002 — Double Ball
Goal: Create a double-ball connector suitable for wrist/torso/neck experimentation.

### KF-UAT-BODY-001 — Split Arm
Goal: Split a continuous arm mesh into upper arm and forearm.

### KF-UAT-HINGE-001 — Elbow
Goal: Create a printable elbow articulation.

### KF-UAT-HINGE-002 — Double-Hinge Knee
Goal: Create a high-range knee prototype.

### KF-UAT-MIRROR-001 — Symmetry
Goal: Mirror a tested left-side joint to the right side.

### KF-UAT-TEST-001 — Range Preview
Goal: Preview a joint from minimum to maximum angle.

### KF-UAT-PRINT-001 — Export
Goal: Export a multi-part figure setup.

---

## Required Tester Feedback

For each feature:
1. Would you use this instead of manual Blender workflow?
2. Which clicks are unnecessary?
3. Which parameter names feel wrong?
4. Does the joint look acceptable on a collectible figure?
5. What would prevent this from being production-usable?
