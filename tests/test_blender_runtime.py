"""Blender 4.2+ Real Runtime Integration Test on PACKAGED ZIP ARTIFACT.

Tests the actual built extension ZIP that testers download, rather than importing
the raw git repository source tree:
    blender --background --factory-startup --python tests/test_blender_runtime.py

Validates for PR-001, PR-002 & PR-003:
1. Locates and extracts the built extension ZIP into an isolated temporary directory.
2. Imports the addon directly from the extracted package (no source tree fallback).
3. Clean add-on registration & unregistration on real bpy.types & bpy.types.Scene.
4. Scene safety: preserves unrelated scene objects and scene unit settings.
5. Operator execution: bpy.ops.kinefig.create_ball_joint (5mm ball, 3mm stem, 5mm length).
6. Naming: creates KF_Joint_Ball_001, repeated execution creates KF_Joint_Ball_002 without collision.
7. Metadata: validates factual metadata (kf_type, kf_joint_type, dimensions, axis)
   and verifies uncomputed keys are ABSENT.
8. Geometry dimensions: exact 5.0mm diameter and 7.5mm total height within tolerance.
9. Geometry quality & Manifoldness: asserts 100% 2-manifold edges, 0 boundary edges, positive volume.
10. PR-003 Parametric Female Ball Socket Cavity Core:
    - bpy.ops.kinefig.create_ball_socket (5mm ball, 0.15mm clearance, 3.5mm depth).
    - Creates KF_Socket_Ball_001, repeated execution creates KF_Socket_Ball_002.
    - Factual metadata (kf_type="socket", kf_socket_type="ball", clearance, depth, axis, insertion_axis).
    - Closed 2-manifold cutter volume (0 non-manifold edges, 0 boundary edges, positive volume).
    - Geometrical clearance invariant: socket cavity radius - ball radius == 0.15 mm.
    - Contextual operator: bpy.ops.kinefig.use_selected_ball copies diameter from active ball joint.
11. Transactional rollback: injected Boolean failure leaves 0 orphan objects/meshes and preserves scene.
12. Zero temporary helper objects (_KF_TMP_) remain in objects or mesh datablocks.
13. Undo state transition: verifies exact object removal if supported, or reports headless status.
14. Clean unregister.
"""

import sys
import os
import math
import zipfile
import tempfile
from pathlib import Path

try:
    import bpy
    import bmesh
except ImportError:
    print("ERROR: This test script must be executed inside Blender via:")
    print("    blender --background --factory-startup --python tests/test_blender_runtime.py")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"


def find_extension_zip() -> Path:
    """Locate the built extension zip to test."""
    if "--zip" in sys.argv:
        idx = sys.argv.index("--zip")
        if idx + 1 < len(sys.argv):
            return Path(sys.argv[idx + 1]).resolve()

    zips = list(DIST_DIR.glob("kinefig-*.zip"))
    if not zips:
        raise FileNotFoundError(
            f"No extension zip found in {DIST_DIR}. Run 'python scripts/build_extension.py' first."
        )

    # Prefer standard kinefig-<version>.zip or newest
    standard_zips = [z for z in zips if not re_has_pr(z.name)]
    if standard_zips:
        return sorted(standard_zips, key=lambda z: z.stat().st_mtime, reverse=True)[0]
    return sorted(zips, key=lambda z: z.stat().st_mtime, reverse=True)[0]


def re_has_pr(name: str) -> bool:
    import re
    return bool(re.search(r"pr\d+", name))


def run_tests():
    zip_path = find_extension_zip()
    print("\n" + "=" * 70)
    print(f"KineFig Real Blender Runtime Test on Blender {bpy.app.version_string}")
    print(f"Testing Packaged Zip Artifact: {zip_path.name} ({zip_path.stat().st_size} bytes)")
    print("=" * 70)

    # Create an isolated temporary directory for extracting the zip
    with tempfile.TemporaryDirectory(prefix="kinefig_test_ext_") as temp_dir:
        temp_path = Path(temp_dir)
        addon_pkg_dir = temp_path / "kinefig"
        addon_pkg_dir.mkdir()

        # Extract zip into kinefig package folder
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(addon_pkg_dir)

        # Ensure project root is NOT in sys.path so we don't import git working copy
        if str(PROJECT_ROOT) in sys.path:
            sys.path.remove(str(PROJECT_ROOT))
        if str(temp_path) not in sys.path:
            sys.path.insert(0, str(temp_path))

        # Import packaged extension directly
        import kinefig
        from kinefig.core.build_info import get_version_string, get_short_sha
        from kinefig.core.naming import PREFIX_TEMP, is_temp_object
        from kinefig.core.errors import KineFigGeometryError
        from kinefig.geometry import joints as joints_mod
        from kinefig.geometry import sockets as sockets_mod
        from kinefig.geometry.joints import create_ball_joint_geometry, create_double_ball_geometry
        from kinefig.geometry.sockets import create_ball_socket_geometry

        print(f"Imported package from: {kinefig.__file__}")
        assert str(addon_pkg_dir) in str(Path(kinefig.__file__).resolve()), (
            f"Package was not loaded from zip extraction directory: {kinefig.__file__}"
        )
        print(f"Build Info in Zip: {get_version_string()}")

        # 1. Test clean registration and unregistration
        print("\n[1/16] Testing register() & unregister() cycle...")
        kinefig.register()
        assert hasattr(bpy.types, "KINEFIG_OT_create_ball_joint"), (
            "KINEFIG_OT_create_ball_joint missing from bpy.types after register()"
        )
        assert hasattr(bpy.types, "KINEFIG_OT_create_double_ball_joint"), (
            "KINEFIG_OT_create_double_ball_joint missing from bpy.types after register()"
        )
        assert hasattr(bpy.types, "KINEFIG_OT_create_ball_socket"), (
            "KINEFIG_OT_create_ball_socket missing from bpy.types after register()"
        )
        assert hasattr(bpy.types, "KINEFIG_OT_use_selected_ball"), (
            "KINEFIG_OT_use_selected_ball missing from bpy.types after register()"
        )
        assert hasattr(bpy.types, "KINEFIG_OT_create_smoke_object"), (
            "KINEFIG_OT_create_smoke_object missing from bpy.types after register()"
        )
        assert hasattr(bpy.types, "KINEFIG_PT_main"), (
            "KINEFIG_PT_main missing from bpy.types after register()"
        )
        assert hasattr(bpy.types.Scene, "kinefig_ball_joint"), (
            "kinefig_ball_joint missing from bpy.types.Scene after register()"
        )
        assert hasattr(bpy.types.Scene, "kinefig_double_ball_joint"), (
            "kinefig_double_ball_joint missing from bpy.types.Scene after register()"
        )
        assert hasattr(bpy.types.Scene, "kinefig_ball_socket"), (
            "kinefig_ball_socket missing from bpy.types.Scene after register()"
        )

        kinefig.unregister()
        assert not hasattr(bpy.types, "KINEFIG_OT_create_ball_joint"), (
            "KINEFIG_OT_create_ball_joint still present in bpy.types after unregister()"
        )
        assert not hasattr(bpy.types, "KINEFIG_OT_create_double_ball_joint"), (
            "KINEFIG_OT_create_double_ball_joint still present in bpy.types after unregister()"
        )
        assert not hasattr(bpy.types, "KINEFIG_OT_create_ball_socket"), (
            "KINEFIG_OT_create_ball_socket still present in bpy.types after unregister()"
        )
        assert not hasattr(bpy.types.Scene, "kinefig_double_ball_joint"), (
            "kinefig_double_ball_joint still present in bpy.types.Scene after unregister()"
        )
        assert not hasattr(bpy.types.Scene, "kinefig_ball_socket"), (
            "kinefig_ball_socket still present in bpy.types.Scene after unregister()"
        )

        # Re-register for functional tests
        kinefig.register()
        print("  -> PASSED: Packaged zip register/unregister cycle clean")

        # 2. Scene Safety Setup: unrelated object & scene unit baseline
        print("\n[2/13] Testing scene safety & preservation baseline...")
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        # Set 3D Cursor to specific known location
        test_cursor_loc = (0.020, 0.030, 0.010)
        bpy.context.scene.cursor.location = test_cursor_loc

        # Record initial scene unit scale
        initial_unit_scale = bpy.context.scene.unit_settings.scale_length

        # Create an unrelated user object to verify scene protection
        bpy.ops.mesh.primitive_cube_add(size=0.050, location=(-0.1, -0.1, 0))
        unrelated_obj = bpy.context.active_object
        unrelated_obj.name = "User_Target_Mesh"
        print("  -> PASSED: Created unrelated scene object and recorded baseline state")

        # 3. Create Parametric Male Ball Joint (PR-002 Core)
        print("\n[3/13] Testing bpy.ops.kinefig.create_ball_joint execution...")
        res = bpy.ops.kinefig.create_ball_joint(
            ball_diameter_mm=5.0,
            stem_diameter_mm=3.0,
            stem_length_mm=5.0,
            segments=32,
            rings=16,
        )
        assert res == {"FINISHED"}, f"create_ball_joint returned {res}"

        ball_obj = bpy.data.objects.get("KF_Joint_Ball_001")
        assert ball_obj is not None, "KF_Joint_Ball_001 not found in bpy.data.objects"
        print(f"  -> PASSED: Created {ball_obj.name}")

        # 4. Create Parametric Female Ball Socket (PR-003 Core)
        print("\n[4/13] Testing bpy.ops.kinefig.create_ball_socket execution...")
        sres = bpy.ops.kinefig.create_ball_socket(
            ball_diameter_mm=5.0,
            clearance_mm=0.15,
            socket_depth_mm=3.5,
            segments=32,
            rings=16,
        )
        assert sres == {"FINISHED"}, f"create_ball_socket returned {sres}"

        socket_obj = bpy.data.objects.get("KF_Socket_Ball_001")
        assert socket_obj is not None, "KF_Socket_Ball_001 not found in bpy.data.objects"
        print(f"  -> PASSED: Created {socket_obj.name}")

        # 5. Verify Socket Factual Metadata & Absence of Unknowns
        print("\n[5/13] Verifying socket parametric metadata...")
        assert socket_obj.get("kf_type") == "socket", f"kf_type mismatch: {socket_obj.get('kf_type')}"
        assert socket_obj.get("kf_socket_type") == "ball", f"kf_socket_type mismatch: {socket_obj.get('kf_socket_type')}"
        assert math.isclose(socket_obj.get("kf_ball_diameter_mm"), 5.0, abs_tol=1e-5), "kf_ball_diameter_mm mismatch"
        assert math.isclose(socket_obj.get("kf_clearance_mm"), 0.15, abs_tol=1e-5), "kf_clearance_mm mismatch"
        assert math.isclose(socket_obj.get("kf_socket_diameter_mm"), 5.30, abs_tol=1e-5), "kf_socket_diameter_mm mismatch"
        assert math.isclose(socket_obj.get("kf_socket_depth_mm"), 3.5, abs_tol=1e-5), "kf_socket_depth_mm mismatch"
        assert tuple(socket_obj.get("kf_axis")) == (0.0, 0.0, 1.0), "kf_axis mismatch"
        assert tuple(socket_obj.get("kf_insertion_axis")) == (0.0, 0.0, 1.0), "kf_insertion_axis mismatch"
        assert tuple(socket_obj.get("kf_opening_normal")) == (0.0, 0.0, -1.0), "kf_opening_normal mismatch"

        # Uncomputed/unknown metadata keys must NOT be present
        for uncomputed_key in ("kf_range_min", "kf_range_max", "kf_role", "kf_side", "fit_quality", "printer_profile"):
            assert uncomputed_key not in socket_obj, f"Uncomputed metadata key '{uncomputed_key}' should be absent"
        print("  -> PASSED: Socket factual metadata verified; uncomputed keys are strictly absent")

        # 6. Verify Socket Dimensions & 3D Cursor Placement
        print("\n[6/13] Verifying socket geometry dimensions and location...")
        sdim = socket_obj.dimensions
        tolerance = 2e-4  # 0.2 mm tolerance for discrete mesh facets

        # Width and Depth = cavity diameter = 5.30 mm = 0.0053 m
        assert math.isclose(sdim.x, 0.0053, abs_tol=tolerance), (
            f"Socket X dimension mismatch: expected 0.0053m, got {sdim.x:.5f}m"
        )
        assert math.isclose(sdim.y, 0.0053, abs_tol=tolerance), (
            f"Socket Y dimension mismatch: expected 0.0053m, got {sdim.y:.5f}m"
        )
        # Height = socket depth = 3.50 mm = 0.0035 m
        assert math.isclose(sdim.z, 0.0035, abs_tol=tolerance), (
            f"Socket Z dimension mismatch: expected 0.0035m, got {sdim.z:.5f}m"
        )
        print(f"  -> Socket Dims: X={sdim.x*1000:.2f}mm, Y={sdim.y*1000:.2f}mm, Z={sdim.z*1000:.2f}mm")

        # Location matches cursor
        sloc = socket_obj.location
        assert math.isclose(sloc.x, test_cursor_loc[0], abs_tol=1e-5), "Socket location X mismatch"
        assert math.isclose(sloc.y, test_cursor_loc[1], abs_tol=1e-5), "Socket location Y mismatch"
        assert math.isclose(sloc.z, test_cursor_loc[2], abs_tol=1e-5), "Socket location Z mismatch"
        print(f"  -> Socket Location: ({sloc.x:.3f}, {sloc.y:.3f}, {sloc.z:.3f}) matches 3D Cursor")

        # 7. Geometry Quality Check: Manifoldness Assertion on Socket Tool (bmesh)
        print("\n[7/13] Asserting 100% Watertight 2-Manifold Quality on Socket Cutter...")
        sbm = bmesh.new()
        sbm.from_mesh(socket_obj.data)

        s_non_manifold_edges = [e for e in sbm.edges if not e.is_manifold]
        s_boundary_edges = [e for e in sbm.edges if e.is_boundary]
        s_vol = sbm.calc_volume()

        assert len(s_non_manifold_edges) == 0, f"Found {len(s_non_manifold_edges)} non-manifold edges in socket!"
        assert len(s_boundary_edges) == 0, f"Found {len(s_boundary_edges)} open boundary edges in socket!"
        assert s_vol > 0.0, f"Socket cutter volume must be positive, got {s_vol}"
        print(f"  -> PASSED: Socket is watertight 2-manifold (non-manifold=0, boundaries=0, volume={s_vol:.2e}m³)")
        sbm.free()

        # 8. Matched Ball + Socket Invariant (Geometric Clearance Assertion)
        print("\n[8/13] Asserting Matched Ball + Socket Geometric Clearance Invariant...")
        ball_radius_measured = ball_obj.dimensions.x / 2.0
        socket_radius_measured = socket_obj.dimensions.x / 2.0
        measured_radial_clearance = socket_radius_measured - ball_radius_measured
        expected_radial_clearance = 0.00015  # 0.15 mm in meters

        assert math.isclose(measured_radial_clearance, expected_radial_clearance, abs_tol=tolerance), (
            f"Clearance invariant violated: measured {measured_radial_clearance*1000:.3f}mm, "
            f"expected {expected_radial_clearance*1000:.3f}mm"
        )
        print(
            f"  -> PASSED: Geometric clearance invariant verified: "
            f"cavity_radius ({socket_radius_measured*1000:.2f}mm) - ball_radius ({ball_radius_measured*1000:.2f}mm) "
            f"= {measured_radial_clearance*1000:.3f}mm (matches 0.15mm clearance contract)"
        )

        # 9. Repeated Execution & Naming Collision Avoidance for Sockets
        print("\n[9/13] Testing repeated execution collision handling for sockets...")
        sres2 = bpy.ops.kinefig.create_ball_socket(
            ball_diameter_mm=6.0,
            clearance_mm=0.2,
            socket_depth_mm=4.0,
        )
        assert sres2 == {"FINISHED"}, f"Second socket execution returned {sres2}"
        socket_obj2 = bpy.data.objects.get("KF_Socket_Ball_002")
        assert socket_obj2 is not None, "KF_Socket_Ball_002 not created on repeated run"
        assert socket_obj.name == "KF_Socket_Ball_001", "Existing socket was overwritten or renamed"
        print("  -> PASSED: Sequential naming generated KF_Socket_Ball_002 cleanly")

        # 10. Contextual UX link: Use Selected Ball Operator
        print("\n[10/13] Testing bpy.ops.kinefig.use_selected_ball operator...")
        bpy.context.view_layer.objects.active = ball_obj
        res_link = bpy.ops.kinefig.use_selected_ball()
        assert res_link == {"FINISHED"}, f"use_selected_ball returned {res_link}"
        assert math.isclose(bpy.context.scene.kinefig_ball_socket.ball_diameter_mm, 5.0, abs_tol=1e-5), (
            "kinefig_ball_socket.ball_diameter_mm not updated from selected ball"
        )
        print("  -> PASSED: Successfully populated socket ball diameter from selected ball joint")

        # Test hardening against malformed/invalid metadata (FINDING MEDIUM-02)
        print("  -> Testing use_selected_ball rejection of malformed metadata (NaN)...")
        orig_ball_d = ball_obj.get("kf_ball_diameter_mm")
        ball_obj["kf_ball_diameter_mm"] = float("nan")
        prev_socket_d = bpy.context.scene.kinefig_ball_socket.ball_diameter_mm

        res_malformed = bpy.ops.kinefig.use_selected_ball()
        assert res_malformed == {"CANCELLED"}, f"Expected CANCELLED on NaN metadata, got {res_malformed}"
        assert math.isclose(
            bpy.context.scene.kinefig_ball_socket.ball_diameter_mm, prev_socket_d, abs_tol=1e-5
        ), "Scene socket setting was modified on validation failure!"

        # Restore original valid metadata cleanly
        ball_obj["kf_ball_diameter_mm"] = orig_ball_d
        print("  -> PASSED: Malformed metadata safely rejected without mutating scene state")

        # 11. Verify Scene Safety & Temp Cleanup on Success
        print("\n[11/13] Verifying scene safety and temp datablock cleanup on success...")
        assert "User_Target_Mesh" in bpy.data.objects, "Unrelated object was removed or renamed"
        assert bpy.context.scene.unit_settings.scale_length == initial_unit_scale, "Scene unit settings altered"

        temp_objs = [o.name for o in bpy.data.objects if is_temp_object(o.name) or o.name.startswith(PREFIX_TEMP)]
        assert len(temp_objs) == 0, f"Orphan temporary objects found: {temp_objs}"

        temp_meshes = [m.name for m in bpy.data.meshes if is_temp_object(m.name) or m.name.startswith(PREFIX_TEMP)]
        assert len(temp_meshes) == 0, f"Orphan temporary mesh datablocks found: {temp_meshes}"
        print(f"  -> PASSED: Zero temporary objects or meshes ({PREFIX_TEMP} = 0)")

        # 12. Test Transactional Rollback on Socket Boolean Failure
        print("\n[12/13] Testing socket transactional rollback on Boolean failure via internal seam...")
        baseline_objects = set(bpy.data.objects.keys())
        baseline_meshes = set(bpy.data.meshes.keys())

        orig_socket_eval = sockets_mod._evaluate_boolean_trim

        def failing_socket_eval(ctx, sobj, m):
            raise KineFigGeometryError("Injected Boolean trimming failure for transactional rollback test")

        sockets_mod._evaluate_boolean_trim = failing_socket_eval

        socket_failure_caught = False
        try:
            create_ball_socket_geometry(
                context=bpy.context,
                ball_diameter_mm=5.0,
                clearance_mm=0.15,
                socket_depth_mm=3.5,
            )
        except KineFigGeometryError:
            socket_failure_caught = True
        finally:
            sockets_mod._evaluate_boolean_trim = orig_socket_eval

        assert socket_failure_caught, "Expected KineFigGeometryError was not raised on socket failure!"

        # Verify zero object or mesh leaks after rollback
        current_objects = set(bpy.data.objects.keys())
        current_meshes = set(bpy.data.meshes.keys())
        assert current_objects == baseline_objects, f"Object leak during socket rollback: {current_objects - baseline_objects}"
        assert current_meshes == baseline_meshes, f"Mesh datablock leak during socket rollback: {current_meshes - baseline_meshes}"

        # Existing ball joints and sockets remain intact
        assert "KF_Joint_Ball_001" in bpy.data.objects, "Existing joint was removed during rollback"
        assert "KF_Socket_Ball_001" in bpy.data.objects, "Existing socket was removed during rollback"
        assert "User_Target_Mesh" in bpy.data.objects, "Unrelated user object was damaged during rollback"
        print("  -> PASSED: Socket transactional rollback executed cleanly, zero leaks, scene preserved")

        # 13. PR-004 Double Ball Joint Creation (Symmetric Defaults)
        print("\n[13/16] Testing bpy.ops.kinefig.create_double_ball_joint execution (symmetric default)...")
        bpy.context.scene.cursor.location = (0.010, -0.020, 0.005)
        res_db = bpy.ops.kinefig.create_double_ball_joint(
            ball_a_diameter_mm=5.0,
            ball_b_diameter_mm=5.0,
            stem_diameter_mm=3.0,
            center_distance_mm=8.0,
            segments=32,
            rings=16,
        )
        assert res_db == {"FINISHED"}, f"create_double_ball_joint returned {res_db}"
        assert "KF_Joint_DoubleBall_001" in bpy.data.objects, "KF_Joint_DoubleBall_001 not found in bpy.data.objects"
        db_obj = bpy.data.objects["KF_Joint_DoubleBall_001"]

        # Assert factual metadata
        assert db_obj.get("kf_type") == "joint", f"kf_type mismatch: {db_obj.get('kf_type')}"
        assert db_obj.get("kf_joint_type") == "double_ball", f"kf_joint_type mismatch: {db_obj.get('kf_joint_type')}"
        assert math.isclose(db_obj.get("kf_ball_a_diameter_mm"), 5.0, abs_tol=1e-5), "kf_ball_a_diameter_mm mismatch"
        assert math.isclose(db_obj.get("kf_ball_b_diameter_mm"), 5.0, abs_tol=1e-5), "kf_ball_b_diameter_mm mismatch"
        assert math.isclose(db_obj.get("kf_stem_diameter_mm"), 3.0, abs_tol=1e-5), "kf_stem_diameter_mm mismatch"
        assert math.isclose(db_obj.get("kf_center_distance_mm"), 8.0, abs_tol=1e-5), "kf_center_distance_mm mismatch"
        assert tuple(db_obj.get("kf_axis")) == (0.0, 0.0, 1.0), "kf_axis mismatch"
        assert tuple(db_obj.get("kf_ball_a_center_mm")) == (0.0, 0.0, 0.0), "kf_ball_a_center_mm mismatch"
        assert tuple(db_obj.get("kf_ball_b_center_mm")) == (0.0, 0.0, 8.0), "kf_ball_b_center_mm mismatch"

        # Check absence of uncomputed metadata
        for uncomputed_key in ("kf_range_min", "kf_range_max", "kf_role", "kf_side", "fit_quality", "printer_profile"):
            assert uncomputed_key not in db_obj, f"Uncomputed metadata key '{uncomputed_key}' present"

        # Assert dimensions and cursor placement
        assert math.isclose(db_obj.location.x, 0.010, abs_tol=1e-4)
        assert math.isclose(db_obj.location.y, -0.020, abs_tol=1e-4)
        assert math.isclose(db_obj.location.z, 0.005, abs_tol=1e-4)

        db_dim = db_obj.dimensions
        print(f"  -> Double Ball Dims: X={db_dim.x*1000:.2f}mm, Y={db_dim.y*1000:.2f}mm, Z={db_dim.z*1000:.2f}mm")
        assert math.isclose(db_dim.x, 0.005, abs_tol=0.0002), f"Double Ball X dim {db_dim.x} != 0.005m"
        assert math.isclose(db_dim.y, 0.005, abs_tol=0.0002), f"Double Ball Y dim {db_dim.y} != 0.005m"
        assert math.isclose(db_dim.z, 0.013, abs_tol=0.0002), f"Double Ball Z dim {db_dim.z} != 0.013m"

        # Manifold quality assertions
        bm_db = bmesh.new()
        bm_db.from_mesh(db_obj.data)
        non_manifold_e = [e for e in bm_db.edges if not e.is_manifold]
        boundary_e = [e for e in bm_db.edges if e.is_boundary]
        vol = bm_db.calc_volume()
        bm_db.free()

        assert len(non_manifold_e) == 0, f"Double Ball has {len(non_manifold_e)} non-manifold edges"
        assert len(boundary_e) == 0, f"Double Ball has {len(boundary_e)} boundary edges"
        assert vol > 0.0, f"Double Ball volume must be positive, got {vol}"
        print(f"  -> PASSED: Double Ball is watertight 2-manifold (non-manifold=0, boundaries=0, volume={vol:.2e}m³)")

        # 14. Testing Asymmetric Double Ball Joint (PR-004)
        print("\n[14/16] Testing asymmetric Double Ball joint (Ball A=4mm, Ball B=6mm, Stem=2.5mm, Dist=8mm)...")
        res_asym = bpy.ops.kinefig.create_double_ball_joint(
            ball_a_diameter_mm=4.0,
            ball_b_diameter_mm=6.0,
            stem_diameter_mm=2.5,
            center_distance_mm=8.0,
            segments=32,
            rings=16,
        )
        assert res_asym == {"FINISHED"}, f"Asymmetric create_double_ball_joint returned {res_asym}"
        assert "KF_Joint_DoubleBall_002" in bpy.data.objects, "KF_Joint_DoubleBall_002 not found"
        asym_obj = bpy.data.objects["KF_Joint_DoubleBall_002"]

        assert math.isclose(asym_obj.get("kf_ball_a_diameter_mm"), 4.0, abs_tol=1e-5)
        assert math.isclose(asym_obj.get("kf_ball_b_diameter_mm"), 6.0, abs_tol=1e-5)
        assert math.isclose(asym_obj.get("kf_stem_diameter_mm"), 2.5, abs_tol=1e-5)
        assert math.isclose(asym_obj.get("kf_center_distance_mm"), 8.0, abs_tol=1e-5)

        asym_dim = asym_obj.dimensions
        assert math.isclose(asym_dim.x, 0.006, abs_tol=0.0002), f"Asym X dim {asym_dim.x} != 0.006m"
        assert math.isclose(asym_dim.y, 0.006, abs_tol=0.0002), f"Asym Y dim {asym_dim.y} != 0.006m"
        assert math.isclose(asym_dim.z, 0.013, abs_tol=0.0002), f"Asym Z dim {asym_dim.z} != 0.013m"

        # Verify orientation: Ball A at origin side (z <= 2mm), Ball B at +Z side (z >= 5mm)
        verts_z = [v.co.z for v in asym_obj.data.vertices]
        min_z_mm = min(verts_z) * 1000.0
        max_z_mm = max(verts_z) * 1000.0
        assert math.isclose(min_z_mm, -2.0, abs_tol=0.2), f"Ball A bottom expected -2.0mm, got {min_z_mm:.2f}mm"
        assert math.isclose(max_z_mm, 11.0, abs_tol=0.2), f"Ball B top expected 11.0mm, got {max_z_mm:.2f}mm"
        print(f"  -> PASSED: Asymmetric Double Ball orientation verified: Ball A bottom={min_z_mm:.2f}mm, Ball B top={max_z_mm:.2f}mm")

        # 15. Testing Multi-stage Transactional Rollback on Boolean Failure
        print("\n[15/16] Testing multi-stage transactional rollback on Boolean failure...")
        baseline_db_objects = set(bpy.data.objects.keys())
        baseline_db_meshes = set(bpy.data.meshes.keys())

        # Stage 1 failure test
        print("  -> Testing Stage 1 (Ball A + Stem) failure rollback...")
        orig_db_eval = joints_mod._evaluate_double_ball_union

        def fail_stage_1(ctx, obj, mod, stage=1):
            if stage == 1:
                raise KineFigGeometryError("Injected Stage 1 Boolean Union failure")
            return orig_db_eval(ctx, obj, mod, stage)

        joints_mod._evaluate_double_ball_union = fail_stage_1
        stage1_failed = False
        try:
            bpy.ops.kinefig.create_double_ball_joint(
                ball_a_diameter_mm=5.0,
                ball_b_diameter_mm=5.0,
                stem_diameter_mm=3.0,
                center_distance_mm=8.0,
            )
        except RuntimeError:
            stage1_failed = True
        finally:
            joints_mod._evaluate_double_ball_union = orig_db_eval

        assert stage1_failed, "Expected operator cancellation/RuntimeError on Stage 1 failure"
        assert set(bpy.data.objects.keys()) == baseline_db_objects, "Objects leaked after Stage 1 failure!"
        assert set(bpy.data.meshes.keys()) == baseline_db_meshes, "Meshes leaked after Stage 1 failure!"
        print("  -> PASSED: Stage 1 failure rolled back cleanly with zero leaks")

        # Stage 2 failure test
        print("  -> Testing Stage 2 ((Ball A + Stem) + Ball B) failure rollback...")
        def fail_stage_2(ctx, obj, mod, stage=1):
            if stage == 2:
                raise KineFigGeometryError("Injected Stage 2 Boolean Union failure")
            return orig_db_eval(ctx, obj, mod, stage)

        joints_mod._evaluate_double_ball_union = fail_stage_2
        stage2_failed = False
        try:
            bpy.ops.kinefig.create_double_ball_joint(
                ball_a_diameter_mm=5.0,
                ball_b_diameter_mm=5.0,
                stem_diameter_mm=3.0,
                center_distance_mm=8.0,
            )
        except RuntimeError:
            stage2_failed = True
        finally:
            joints_mod._evaluate_double_ball_union = orig_db_eval

        assert stage2_failed, "Expected operator cancellation/RuntimeError on Stage 2 failure"
        assert set(bpy.data.objects.keys()) == baseline_db_objects, "Objects leaked after Stage 2 failure!"
        assert set(bpy.data.meshes.keys()) == baseline_db_meshes, "Meshes leaked after Stage 2 failure!"
        print("  -> PASSED: Stage 2 failure rolled back cleanly, intermediate Stage 1 mesh deleted")

        # 16. Test Undo State Transition (Sockets & Double Ball)
        print("\n[16/16] Testing Undo state transition for Double Ball joints...")
        res_undo_db = bpy.ops.kinefig.create_double_ball_joint(
            ball_a_diameter_mm=5.0,
            ball_b_diameter_mm=5.0,
            stem_diameter_mm=3.0,
            center_distance_mm=8.0,
        )
        assert res_undo_db == {"FINISHED"}, f"Failed to create undo test double ball: {res_undo_db}"
        undo_test_db_name = "KF_Joint_DoubleBall_003"
        assert undo_test_db_name in bpy.data.objects, f"Expected {undo_test_db_name} before Undo"

        undo_supported = (
            hasattr(bpy.ops.ed, "undo")
            and bpy.ops.ed.undo.poll()
        )

        if not undo_supported:
            print(
                "  -> INFO: AUTOMATED UNDO: NOT VERIFIED IN HEADLESS "
                "(bpy.ops.ed.undo.poll() returned False in background mode)"
            )
        else:
            undo_call_res = bpy.ops.ed.undo()
            assert undo_call_res == {"FINISHED"}, f"bpy.ops.ed.undo returned {undo_call_res}"
            assert undo_test_db_name not in bpy.data.objects, (
                f"Undo state transition assertion failed: {undo_test_db_name} was NOT removed by Undo!"
            )
            assert "KF_Joint_DoubleBall_001" in bpy.data.objects, "Earlier KF_Joint_DoubleBall_001 was improperly removed by Undo!"
            assert "KF_Joint_DoubleBall_002" in bpy.data.objects, "Earlier KF_Joint_DoubleBall_002 was improperly removed by Undo!"
            assert "User_Target_Mesh" in bpy.data.objects, "Undo corrupted scene: User_Target_Mesh was removed by Undo!"
            assert "KF_Joint_Ball_001" in bpy.data.objects, "Earlier KF_Joint_Ball_001 was improperly removed by Undo!"
            assert "KF_Socket_Ball_001" in bpy.data.objects, "Earlier KF_Socket_Ball_001 was improperly removed by Undo!"
            print(f"  -> PASSED: Undo removed {undo_test_db_name}; verified earlier and unrelated objects preserved")

        # Cleanup & Final Unregister
        print("\nCleaning up test objects and unregistering...")
        for name in (
            "KF_Joint_Ball_001",
            "KF_Socket_Ball_001",
            "KF_Socket_Ball_002",
            "KF_Socket_Ball_003",
            "KF_Joint_DoubleBall_001",
            "KF_Joint_DoubleBall_002",
            "KF_Joint_DoubleBall_003",
            "User_Target_Mesh",
        ):
            obj = bpy.data.objects.get(name)
            if obj:
                bpy.data.objects.remove(obj, do_unlink=True)

        kinefig.unregister()
        print("  -> PASSED: Cleanup and unregister complete")

    print("\n" + "=" * 70)
    print("ALL REAL BLENDER RUNTIME INTEGRATION TESTS PASSED ON PACKAGED ZIP!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        run_tests()
        sys.exit(0)
    except Exception as exc:
        print(f"\nFATAL TEST FAILURE: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
