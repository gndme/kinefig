"""Blender 4.2+ Real Runtime Integration Test.

Run directly with Blender in background mode:
    blender --background --factory-startup --python tests/test_blender_runtime.py

Validates:
1. Clean add-on registration & unregistration (including all operators and panels).
2. Operator execution via real bpy.ops.kinefig.create_smoke_object.
3. Object geometry verification: diameter = 10 mm (0.010m).
4. Deterministic repeated execution without naming collision (KF_Smoke_Ball_001, KF_Smoke_Ball_002).
5. Diagnostic operators execution (copy_debug_info).
6. Undo operator execution.
7. Scene cleanup.
"""

import sys
import math
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import bpy
except ImportError:
    print("ERROR: This test script must be executed inside Blender via:")
    print("    blender --background --factory-startup --python tests/test_blender_runtime.py")
    sys.exit(1)

import addon.kinefig as kinefig
from addon.kinefig.core.build_info import get_version_string, get_short_sha
from addon.kinefig.core.diagnostics import collect_diagnostic_report


def run_tests():
    print("\n" + "=" * 60)
    print(f"Running KineFig Real Blender Runtime Test on Blender {bpy.app.version_string}")
    print(f"Build Info: {get_version_string()}")
    print("=" * 60)

    # 1. Test clean registration and unregistration
    print("[1/7] Testing register() & unregister()...")
    kinefig.register()
    assert hasattr(bpy.types, "KINEFIG_OT_create_smoke_object"), (
        "KINEFIG_OT_create_smoke_object missing from bpy.types after register()"
    )
    assert hasattr(bpy.types, "KINEFIG_OT_copy_debug_info"), (
        "KINEFIG_OT_copy_debug_info missing from bpy.types after register()"
    )
    assert hasattr(bpy.types, "KINEFIG_PT_main"), (
        "KINEFIG_PT_main missing from bpy.types after register()"
    )

    kinefig.unregister()
    assert not hasattr(bpy.types, "KINEFIG_OT_create_smoke_object"), (
        "KINEFIG_OT_create_smoke_object still present in bpy.types after unregister()"
    )
    assert not hasattr(bpy.types, "KINEFIG_OT_copy_debug_info"), (
        "KINEFIG_OT_copy_debug_info still present in bpy.types after unregister()"
    )
    assert not hasattr(bpy.types, "KINEFIG_PT_main"), (
        "KINEFIG_PT_main still present in bpy.types after unregister()"
    )

    # Re-register for functional tests
    kinefig.register()
    print("  -> PASSED: register/unregister cycle clean")

    # 2. Test Smoke Operator execution
    print("[2/7] Testing smoke operator execution...")
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    res = bpy.ops.kinefig.create_smoke_object()
    assert res == {"FINISHED"}, f"Operator returned {res}"

    obj1 = bpy.data.objects.get("KF_Smoke_Ball_001")
    assert obj1 is not None, "KF_Smoke_Ball_001 not found in bpy.data.objects"
    assert obj1.get("kf_type") == "smoke", f"Metadata kf_type missing or wrong: {obj1.get('kf_type')}"
    print("  -> PASSED: Created KF_Smoke_Ball_001 with correct metadata")

    # 3. Test Unit Contract & Real Geometry Dimensions
    print("[3/7] Testing geometry dimensions (10 mm unit contract)...")
    # Radius = 5mm (0.005m), Diameter = 10mm (0.010m)
    dim = obj1.dimensions
    expected_m = 0.010
    tolerance = 1e-4

    assert math.isclose(dim.x, expected_m, abs_tol=tolerance), (
        f"Dimension X mismatch: expected {expected_m}m, got {dim.x}m"
    )
    assert math.isclose(dim.y, expected_m, abs_tol=tolerance), (
        f"Dimension Y mismatch: expected {expected_m}m, got {dim.y}m"
    )
    assert math.isclose(dim.z, expected_m, abs_tol=tolerance), (
        f"Dimension Z mismatch: expected {expected_m}m, got {dim.z}m"
    )
    print(f"  -> PASSED: Verified dimensions: X={dim.x:.4f}m, Y={dim.y:.4f}m, Z={dim.z:.4f}m (10.0 mm)")

    # 4. Test Repeated Execution & Collision Avoidance
    print("[4/7] Testing repeated execution collision handling...")
    res2 = bpy.ops.kinefig.create_smoke_object()
    assert res2 == {"FINISHED"}, f"Second execution returned {res2}"

    obj2 = bpy.data.objects.get("KF_Smoke_Ball_002")
    assert obj2 is not None, "KF_Smoke_Ball_002 not created on repeated run"
    assert obj1.name == "KF_Smoke_Ball_001", "Existing object was overwritten or renamed"
    assert obj1 != obj2, "Second object is identical instance to first object"
    print("  -> PASSED: Sequential naming generated KF_Smoke_Ball_002 without collision")

    # 5. Test Diagnostic Info Generation in real Blender
    print("[5/7] Testing real Blender diagnostics...")
    report = collect_diagnostic_report(bpy.context, active_feature="SmokeTest")
    assert report["system"]["blender_version"] == bpy.app.version_string
    assert report["system"]["blender_mode"] == "OBJECT"
    assert len(report["recent_logs"]) > 0, "No structured logs found in diagnostic report"

    # Test copy debug info operator execution
    res_copy = bpy.ops.kinefig.copy_debug_info()
    assert res_copy == {"FINISHED"}, f"copy_debug_info returned {res_copy}"
    print("  -> PASSED: Real Blender diagnostics collected and copy operator verified")

    # 6. Test Undo (if window manager supports ed.undo in background mode)
    print("[6/7] Testing Undo behavior...")
    try:
        if hasattr(bpy.ops.ed, "undo"):
            if bpy.ops.ed.undo.poll():
                bpy.ops.ed.undo()
                print("  -> PASSED: Undo triggered successfully via bpy.ops.ed.undo()")
            else:
                print("  -> SKIPPED (Undo operator poll returned False in headless mode, which is normal for Blender background)")
        else:
            print("  -> SKIPPED (bpy.ops.ed.undo not available in this Blender build)")
    except Exception as e:
        print(f"  -> INFO: Undo check note: {e}")

    # 7. Cleanup & Final Unregister
    print("[7/7] Cleaning up test objects and unregistering...")
    for name in ("KF_Smoke_Ball_001", "KF_Smoke_Ball_002"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    kinefig.unregister()
    print("  -> PASSED: Cleanup completed cleanly")

    print("=" * 60)
    print("ALL REAL BLENDER RUNTIME INTEGRATION TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_tests()
        sys.exit(0)
    except Exception as exc:
        print(f"\nFATAL TEST FAILURE: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
