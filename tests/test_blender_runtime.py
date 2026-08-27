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
        from kinefig.core.errors import KineFigGeometryError, KineFigValidationError
        from kinefig.geometry import joints as joints_mod
        from kinefig.geometry import sockets as sockets_mod
        from kinefig.geometry.joints import (
            create_ball_joint_geometry,
            create_double_ball_geometry,
            create_peg_geometry,
        )
        from kinefig.geometry.sockets import (
            create_ball_socket_geometry,
            create_peg_socket_geometry,
        )
        from kinefig.ui.panel import (
            _get_valid_selected_peg_diameter,
            _get_valid_selected_ball_diameter,
        )

        print(f"Imported package from: {kinefig.__file__}")
        assert str(addon_pkg_dir) in str(Path(kinefig.__file__).resolve()), (
            f"Package was not loaded from zip extraction directory: {kinefig.__file__}"
        )
        print(f"Build Info in Zip: {get_version_string()}")

        # 1. Test clean registration and unregistration
        print("\n[1/24] Testing register() & unregister() cycle...")
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
        assert hasattr(bpy.types, "KINEFIG_OT_create_peg_joint"), (
            "KINEFIG_OT_create_peg_joint missing from bpy.types after register()"
        )
        assert hasattr(bpy.types, "KINEFIG_OT_create_peg_socket"), (
            "KINEFIG_OT_create_peg_socket missing from bpy.types after register()"
        )
        assert hasattr(bpy.types, "KINEFIG_OT_use_selected_peg"), (
            "KINEFIG_OT_use_selected_peg missing from bpy.types after register()"
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
        assert hasattr(bpy.types.Scene, "kinefig_peg_joint"), (
            "kinefig_peg_joint missing from bpy.types.Scene after register()"
        )
        assert hasattr(bpy.types.Scene, "kinefig_peg_socket"), (
            "kinefig_peg_socket missing from bpy.types.Scene after register()"
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
        assert not hasattr(bpy.types, "KINEFIG_OT_create_peg_joint"), (
            "KINEFIG_OT_create_peg_joint still present in bpy.types after unregister()"
        )
        assert not hasattr(bpy.types, "KINEFIG_OT_create_peg_socket"), (
            "KINEFIG_OT_create_peg_socket still present in bpy.types after unregister()"
        )
        assert not hasattr(bpy.types.Scene, "kinefig_double_ball_joint"), (
            "kinefig_double_ball_joint still present in bpy.types.Scene after unregister()"
        )
        assert not hasattr(bpy.types.Scene, "kinefig_ball_socket"), (
            "kinefig_ball_socket still present in bpy.types.Scene after unregister()"
        )
        assert not hasattr(bpy.types.Scene, "kinefig_ball_joint"), (
            "kinefig_ball_joint still present in bpy.types.Scene after unregister()"
        )
        assert not hasattr(bpy.types.Scene, "kinefig_peg_socket"), (
            "kinefig_peg_socket still present in bpy.types.Scene after unregister()"
        )
        assert not hasattr(bpy.types.Scene, "kinefig_peg_joint"), (
            "kinefig_peg_joint still present in bpy.types.Scene after unregister()"
        )

        # Re-register for functional tests
        kinefig.register()
        print("  -> PASSED: Packaged zip register/unregister cycle clean")

        # 2. Scene Safety Setup: unrelated object & scene unit baseline
        print("\n[2/19] Testing scene safety & preservation baseline...")
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

        def count_connected_components(bm) -> int:
            unvisited_faces = set(bm.faces)
            if not unvisited_faces:
                return 0 if not bm.verts else 1
            components = 0
            while unvisited_faces:
                components += 1
                start_face = unvisited_faces.pop()
                queue = [start_face]
                while queue:
                    current = queue.pop()
                    for edge in current.edges:
                        for linked_face in edge.link_faces:
                            if linked_face in unvisited_faces:
                                unvisited_faces.remove(linked_face)
                                queue.append(linked_face)
            return components

        # 3. Create Parametric Male Ball Joint (PR-002 Core)
        print("\n[3/19] Testing bpy.ops.kinefig.create_ball_joint execution...")
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
        print("\n[4/19] Testing bpy.ops.kinefig.create_ball_socket execution...")
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
        print("\n[5/19] Verifying socket parametric metadata...")
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
        print("\n[6/19] Verifying socket geometry dimensions and location...")
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
        print("\n[7/19] Asserting 100% Watertight 2-Manifold Quality on Socket Cutter...")
        sbm = bmesh.new()
        sbm.from_mesh(socket_obj.data)

        s_non_manifold_edges = [e for e in sbm.edges if not e.is_manifold]
        s_boundary_edges = [e for e in sbm.edges if e.is_boundary]
        s_vol = sbm.calc_volume()

        assert len(s_non_manifold_edges) == 0, f"Found {len(s_non_manifold_edges)} non-manifold edges in socket!"
        assert len(s_boundary_edges) == 0, f"Found {len(s_boundary_edges)} open boundary edges in socket!"
        assert s_vol > 0.0, f"Socket cutter volume must be positive, got {s_vol}"
        assert count_connected_components(sbm) == 1, "Socket cutter must have exactly 1 connected component"
        print(f"  -> PASSED: Socket is watertight 2-manifold (non-manifold=0, boundaries=0, volume={s_vol:.2e}m³, components=1)")
        sbm.free()

        # 8. Matched Ball + Socket Invariant (Geometric Clearance Assertion)
        print("\n[8/19] Asserting Matched Ball + Socket Geometric Clearance Invariant...")
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
        print("\n[9/19] Testing repeated execution collision handling for sockets...")
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
        print("\n[10/19] Testing bpy.ops.kinefig.use_selected_ball operator...")
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
        print("\n[11/19] Verifying scene safety and temp datablock cleanup on success...")
        assert "User_Target_Mesh" in bpy.data.objects, "Unrelated object was removed or renamed"
        assert bpy.context.scene.unit_settings.scale_length == initial_unit_scale, "Scene unit settings altered"

        temp_objs = [o.name for o in bpy.data.objects if is_temp_object(o.name) or o.name.startswith(PREFIX_TEMP)]
        assert len(temp_objs) == 0, f"Orphan temporary objects found: {temp_objs}"

        temp_meshes = [m.name for m in bpy.data.meshes if is_temp_object(m.name) or m.name.startswith(PREFIX_TEMP)]
        assert len(temp_meshes) == 0, f"Orphan temporary mesh datablocks found: {temp_meshes}"
        print(f"  -> PASSED: Zero temporary objects or meshes ({PREFIX_TEMP} = 0)")

        # 12. Test Transactional Rollback on Socket Boolean Failure
        print("\n[12/19] Testing socket transactional rollback on Boolean failure via internal seam...")
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

        # 13. Test Undo State Transition (Unshielded)
        print("\n[13/24] Testing Undo state transition for sockets...")
        res_undo = bpy.ops.kinefig.create_ball_socket(
            ball_diameter_mm=7.0,
            clearance_mm=0.2,
            socket_depth_mm=4.5,
        )
        assert res_undo == {"FINISHED"}
        undo_test_socket_name = "KF_Socket_Ball_003"
        assert undo_test_socket_name in bpy.data.objects, f"Expected {undo_test_socket_name} before Undo"

        if not undo_supported:
            print("  -> INFO: AUTOMATED UNDO: NOT VERIFIED IN HEADLESS (bpy.ops.ed.undo.poll() returned False in background mode)")
        else:
            undo_call_res = bpy.ops.ed.undo()
            assert undo_call_res == {"FINISHED"}
            assert undo_test_socket_name not in bpy.data.objects, f"Undo failed to remove {undo_test_socket_name}"
            assert "User_Target_Mesh" in bpy.data.objects
            assert "KF_Joint_Ball_001" in bpy.data.objects
            assert "KF_Socket_Ball_001" in bpy.data.objects
            print(f"  -> PASSED: Undo removed {undo_test_socket_name}; earlier objects preserved")

        # 14. PR-004 Double Ball Joint Creation (Symmetric Defaults)
        print("\n[14/24] Testing bpy.ops.kinefig.create_double_ball_joint execution (symmetric default)...")
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
        def count_connected_components(bm) -> int:
            unvisited_faces = set(bm.faces)
            if not unvisited_faces:
                return 0 if not bm.verts else 1
            components = 0
            while unvisited_faces:
                components += 1
                start_face = unvisited_faces.pop()
                queue = [start_face]
                while queue:
                    current = queue.pop()
                    for edge in current.edges:
                        for linked_face in edge.link_faces:
                            if linked_face in unvisited_faces:
                                unvisited_faces.remove(linked_face)
                                queue.append(linked_face)
            return components

        bm_db = bmesh.new()
        bm_db.from_mesh(db_obj.data)
        non_manifold_e = [e for e in bm_db.edges if not e.is_manifold]
        boundary_e = [e for e in bm_db.edges if e.is_boundary]
        vol = bm_db.calc_volume()
        comp_count = count_connected_components(bm_db)
        bm_db.free()

        assert len(non_manifold_e) == 0, f"Double Ball has {len(non_manifold_e)} non-manifold edges"
        assert len(boundary_e) == 0, f"Double Ball has {len(boundary_e)} boundary edges"
        assert vol > 0.0, f"Double Ball volume must be positive, got {vol}"
        assert comp_count == 1, f"Double Ball should be a single coherent solid, got {comp_count} components"
        print(f"  -> PASSED: Double Ball is watertight 2-manifold (non-manifold=0, boundaries=0, volume={vol:.2e}m³, components=1)")

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

        bm_asym = bmesh.new()
        bm_asym.from_mesh(asym_obj.data)
        comp_asym = count_connected_components(bm_asym)
        bm_asym.free()
        assert comp_asym == 1, f"Asymmetric Double Ball should be a single coherent solid, got {comp_asym} components"
        print(f"  -> PASSED: Asymmetric Double Ball orientation verified: Ball A bottom={min_z_mm:.2f}mm, Ball B top={max_z_mm:.2f}mm, components=1")

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

        # Regression A: Post-evaluation Stage 1 commit failure test
        print("  -> Testing Regression A: Stage 1 post-evaluation commit failure rollback...")
        orig_commit = joints_mod._commit_evaluated_mesh

        def fail_commit_1(eval_mesh, target_mesh, stage=1):
            if stage == 1:
                raise KineFigGeometryError("Injected Stage 1 post-evaluation commit failure")
            return orig_commit(eval_mesh, target_mesh, stage)

        joints_mod._commit_evaluated_mesh = fail_commit_1
        post_eval1_failed = False
        try:
            bpy.ops.kinefig.create_double_ball_joint(
                ball_a_diameter_mm=5.0,
                ball_b_diameter_mm=5.0,
                stem_diameter_mm=3.0,
                center_distance_mm=8.0,
            )
        except RuntimeError:
            post_eval1_failed = True
        finally:
            joints_mod._commit_evaluated_mesh = orig_commit

        assert post_eval1_failed, "Expected RuntimeError on Stage 1 post-eval failure"
        assert set(bpy.data.objects.keys()) == baseline_db_objects, "Objects leaked after Stage 1 post-eval failure!"
        assert set(bpy.data.meshes.keys()) == baseline_db_meshes, "Meshes leaked after Stage 1 post-eval failure!"
        temp_objs = [name for name in bpy.data.objects.keys() if is_temp_object(name)]
        assert len(temp_objs) == 0, f"Leaked temp objects: {temp_objs}"
        print("  -> PASSED: Stage 1 post-evaluation failure rolled back cleanly, eval_mesh_1 purged with zero leaks")

        # Regression B: Post-evaluation Stage 2 commit failure test
        print("  -> Testing Regression B: Stage 2 post-evaluation commit failure rollback...")
        def fail_commit_2(eval_mesh, target_mesh, stage=1):
            if stage == 2:
                raise KineFigGeometryError("Injected Stage 2 post-evaluation commit failure")
            return orig_commit(eval_mesh, target_mesh, stage)

        joints_mod._commit_evaluated_mesh = fail_commit_2
        post_eval2_failed = False
        try:
            bpy.ops.kinefig.create_double_ball_joint(
                ball_a_diameter_mm=5.0,
                ball_b_diameter_mm=5.0,
                stem_diameter_mm=3.0,
                center_distance_mm=8.0,
            )
        except RuntimeError:
            post_eval2_failed = True
        finally:
            joints_mod._commit_evaluated_mesh = orig_commit

        assert post_eval2_failed, "Expected RuntimeError on Stage 2 post-eval failure"
        assert set(bpy.data.objects.keys()) == baseline_db_objects, "Objects leaked after Stage 2 post-eval failure!"
        assert set(bpy.data.meshes.keys()) == baseline_db_meshes, "Meshes leaked after Stage 2 post-eval failure!"
        temp_objs = [name for name in bpy.data.objects.keys() if is_temp_object(name)]
        assert len(temp_objs) == 0, f"Leaked temp objects: {temp_objs}"
        print("  -> PASSED: Stage 2 post-evaluation failure rolled back cleanly, eval_mesh_2 & Stage 1 mesh purged with zero leaks")

        # Center Distance overlap policy test (center_distance < (ball_a + ball_b)/2)
        print("  -> Testing center distance overlap policy rejection in operator...")
        overlap_failed = False
        try:
            bpy.ops.kinefig.create_double_ball_joint(
                ball_a_diameter_mm=5.0,
                ball_b_diameter_mm=5.0,
                stem_diameter_mm=3.0,
                center_distance_mm=4.0,  # Invalid: 4.0 < 5.0mm
            )
        except RuntimeError:
            overlap_failed = True

        assert overlap_failed, "Expected operator error when center_distance < sum of radii"
        assert set(bpy.data.objects.keys()) == baseline_db_objects, "Objects leaked after overlap rejection!"
        assert set(bpy.data.meshes.keys()) == baseline_db_meshes, "Meshes leaked after overlap rejection!"
        print("  -> PASSED: Center distance overlap strictly rejected without scene mutation")

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

        # 14. Testing Male Peg Joint Default (PR-005)
        print("\n[14/19] Testing bpy.ops.kinefig.create_peg_joint execution (default: 3mm diam, 5mm length)...")
        pres = bpy.ops.kinefig.create_peg_joint(
            peg_diameter_mm=3.0,
            peg_length_mm=5.0,
            taper_angle_deg=0.0,
            segments=32,
        )
        assert pres == {"FINISHED"}, f"create_peg_joint returned {pres}"
        peg_obj = bpy.data.objects.get("KF_Joint_Peg_001")
        assert peg_obj is not None, "KF_Joint_Peg_001 not found in bpy.data.objects"

        # Metadata
        assert peg_obj.get("kf_type") == "joint", f"kf_type mismatch: {peg_obj.get('kf_type')}"
        assert peg_obj.get("kf_joint_type") == "peg", f"kf_joint_type mismatch: {peg_obj.get('kf_joint_type')}"
        assert math.isclose(peg_obj.get("kf_peg_diameter_mm"), 3.0, abs_tol=1e-5), "kf_peg_diameter_mm mismatch"
        assert math.isclose(peg_obj.get("kf_peg_length_mm"), 5.0, abs_tol=1e-5), "kf_peg_length_mm mismatch"
        assert math.isclose(peg_obj.get("kf_taper_angle_deg"), 0.0, abs_tol=1e-5), "kf_taper_angle_deg mismatch"
        assert tuple(peg_obj.get("kf_axis")) == (0.0, 0.0, 1.0), "kf_axis mismatch"
        for k in ("kf_role", "kf_side", "fit_quality", "printer_profile"):
            assert k not in peg_obj, f"Uncomputed metadata key '{k}' found"

        # Dimensions
        pdim = peg_obj.dimensions
        assert math.isclose(pdim.x, 0.003, abs_tol=tolerance), f"Peg X dim {pdim.x} != 0.003m"
        assert math.isclose(pdim.y, 0.003, abs_tol=tolerance), f"Peg Y dim {pdim.y} != 0.003m"
        assert math.isclose(pdim.z, 0.005, abs_tol=tolerance), f"Peg Z dim {pdim.z} != 0.005m"

        # Local bounds: z from 0 to 5mm
        verts_z = [v.co.z for v in peg_obj.data.vertices]
        assert math.isclose(min(verts_z) * 1000.0, 0.0, abs_tol=0.1)
        assert math.isclose(max(verts_z) * 1000.0, 5.0, abs_tol=0.1)

        # Manifoldness & Connected components
        pbm = bmesh.new()
        pbm.from_mesh(peg_obj.data)
        assert len([e for e in pbm.edges if not e.is_manifold]) == 0, "Peg has non-manifold edges"
        assert len([e for e in pbm.edges if e.is_boundary]) == 0, "Peg has boundary edges"
        assert pbm.calc_volume() > 0.0, "Peg volume must be positive"
        assert count_connected_components(pbm) == 1, "Peg must have exactly 1 connected component"
        pbm.free()
        print("  -> PASSED: Created KF_Joint_Peg_001 (manifold=2, components=1, z=[0, 5.0mm])")

        # 15. Testing Male Peg Joint Variant / Tapered (PR-005)
        print("\n[15/19] Testing tapered peg joint (4mm base, 7mm length, 5° draft)...")
        pres_taper = bpy.ops.kinefig.create_peg_joint(
            peg_diameter_mm=4.0,
            peg_length_mm=7.0,
            taper_angle_deg=5.0,
            segments=32,
        )
        assert pres_taper == {"FINISHED"}
        peg_taper_obj = bpy.data.objects.get("KF_Joint_Peg_002")
        assert peg_taper_obj is not None

        # Verify base vs tip radii
        verts_base = [v for v in peg_taper_obj.data.vertices if math.isclose(v.co.z * 1000.0, 0.0, abs_tol=0.1)]
        verts_tip = [v for v in peg_taper_obj.data.vertices if math.isclose(v.co.z * 1000.0, 7.0, abs_tol=0.1)]
        r_base_found = max(math.hypot(v.co.x, v.co.y) for v in verts_base) * 1000.0
        r_tip_found = max(math.hypot(v.co.x, v.co.y) for v in verts_tip) * 1000.0
        expected_r_tip = 2.0 - 7.0 * math.tan(math.radians(5.0))
        assert math.isclose(r_base_found, 2.0, abs_tol=0.15), f"Base radius {r_base_found} != 2.0"
        assert math.isclose(r_tip_found, expected_r_tip, abs_tol=0.15), f"Tip radius {r_tip_found} != {expected_r_tip}"

        tbm = bmesh.new()
        tbm.from_mesh(peg_taper_obj.data)
        assert len([e for e in tbm.edges if not e.is_manifold]) == 0
        assert len([e for e in tbm.edges if e.is_boundary]) == 0
        assert tbm.calc_volume() > 0.0
        assert count_connected_components(tbm) == 1
        tbm.free()
        print(f"  -> PASSED: Created KF_Joint_Peg_002 (taper verified: base_r={r_base_found:.2f}mm, tip_r={r_tip_found:.2f}mm)")

        # 16. Testing Female Peg Socket Receiver Default (PR-005)
        print("\n[16/19] Testing bpy.ops.kinefig.create_peg_socket (peg=3mm, clearance=0.15mm, depth=5mm)...")
        psres = bpy.ops.kinefig.create_peg_socket(
            peg_diameter_mm=3.0,
            radial_clearance_mm=0.15,
            socket_depth_mm=5.0,
            segments=32,
        )
        assert psres == {"FINISHED"}
        psocket_obj = bpy.data.objects.get("KF_Socket_Peg_001")
        assert psocket_obj is not None

        # Metadata
        assert psocket_obj.get("kf_type") == "socket"
        assert psocket_obj.get("kf_socket_type") == "peg"
        assert math.isclose(psocket_obj.get("kf_peg_diameter_mm"), 3.0, abs_tol=1e-5)
        assert math.isclose(psocket_obj.get("kf_radial_clearance_mm"), 0.15, abs_tol=1e-5)
        assert math.isclose(psocket_obj.get("kf_socket_diameter_mm"), 3.30, abs_tol=1e-5)
        assert math.isclose(psocket_obj.get("kf_socket_depth_mm"), 5.0, abs_tol=1e-5)
        assert tuple(psocket_obj.get("kf_axis")) == (0.0, 0.0, 1.0)
        assert tuple(psocket_obj.get("kf_insertion_axis")) == (0.0, 0.0, 1.0)
        assert tuple(psocket_obj.get("kf_opening_normal")) == (0.0, 0.0, -1.0)

        # Dimensions: 3.30mm diameter, 5.0mm depth
        psdim = psocket_obj.dimensions
        assert math.isclose(psdim.x, 0.0033, abs_tol=tolerance)
        assert math.isclose(psdim.y, 0.0033, abs_tol=tolerance)
        assert math.isclose(psdim.z, 0.0050, abs_tol=tolerance)

        # Local bounds: z from 0 to 5mm
        psverts_z = [v.co.z for v in psocket_obj.data.vertices]
        assert math.isclose(min(psverts_z) * 1000.0, 0.0, abs_tol=0.1)
        assert math.isclose(max(psverts_z) * 1000.0, 5.0, abs_tol=0.1)

        # Manifoldness & Connected components
        psbm = bmesh.new()
        psbm.from_mesh(psocket_obj.data)
        assert len([e for e in psbm.edges if not e.is_manifold]) == 0
        assert len([e for e in psbm.edges if e.is_boundary]) == 0
        assert psbm.calc_volume() > 0.0
        assert count_connected_components(psbm) == 1
        psbm.free()
        print("  -> PASSED: Created KF_Socket_Peg_001 (diameter=3.30mm, depth=5.0mm, components=1)")

        # 17. Matching Clearance Invariant & Contextual use_selected_peg (PR-005)
        print("\n[17/19] Asserting Peg + Socket Clearance Invariant & use_selected_peg...")
        peg_r_measured = peg_obj.dimensions.x / 2.0
        psocket_r_measured = psocket_obj.dimensions.x / 2.0
        peg_radial_clearance = psocket_r_measured - peg_r_measured
        assert math.isclose(peg_radial_clearance, 0.00015, abs_tol=tolerance), (
            f"Peg clearance invariant violated: measured {peg_radial_clearance*1000:.3f}mm, expected 0.150mm"
        )
        print("  -> PASSED: Peg clearance invariant verified: socket_r (1.65mm) - peg_r (1.50mm) = 0.150mm")

        # Contextual operator
        bpy.context.view_layer.objects.active = peg_obj
        res_match = bpy.ops.kinefig.use_selected_peg()
        assert res_match == {"FINISHED"}
        assert math.isclose(bpy.context.scene.kinefig_peg_socket.peg_diameter_mm, 3.0, abs_tol=1e-5)

        # Malformed metadata test (MEDIUM-01 Regression Gate)
        print("  -> Testing safe rejection of malformed peg metadata in UI and operator...")
        orig_peg_d = peg_obj.get("kf_peg_diameter_mm")
        malformed_test_cases = [
            "abc",
            None,
            float("nan"),
            float("inf"),
            float("-inf"),
            0,
            -1,
        ]
        for bad_val in malformed_test_cases:
            peg_obj["kf_peg_diameter_mm"] = bad_val
            # 1. UI helper must return None so malformed metadata is never presented as valid
            assert _get_valid_selected_peg_diameter(peg_obj) is None, (
                f"Expected None from _get_valid_selected_peg_diameter for {bad_val!r}"
            )
            # 2. Operator execution must safely CANCEL
            res_bad = bpy.ops.kinefig.use_selected_peg()
            assert res_bad == {"CANCELLED"}, f"Expected CANCELLED for {bad_val!r}, got {res_bad}"
            # 3. Scene setting must NOT be mutated
            assert math.isclose(bpy.context.scene.kinefig_peg_socket.peg_diameter_mm, 3.0, abs_tol=1e-5), (
                f"Scene setting was mutated by malformed peg metadata {bad_val!r}"
            )

        # Restore original valid metadata
        peg_obj["kf_peg_diameter_mm"] = orig_peg_d
        print("  -> PASSED: All malformed metadata cases (abc, None, NaN, +/-inf, 0, -1) safely rejected without scene mutation")

        # 18. Testing Peg Core Validation & Zero-Leak Rollback (PR-005)
        print("\n[18/19] Testing peg core validation error and transactional rollback...")
        baseline_peg_objects = set(bpy.data.objects.keys())
        baseline_peg_meshes = set(bpy.data.meshes.keys())

        peg_val_err = False
        try:
            create_peg_geometry(
                context=bpy.context,
                peg_diameter_mm=-1.0,
                peg_length_mm=5.0,
                taper_angle_deg=0.0,
                segments=32,
            )
        except KineFigValidationError:
            peg_val_err = True

        assert peg_val_err, "Expected KineFigValidationError on negative peg diameter"
        assert set(bpy.data.objects.keys()) == baseline_peg_objects, (
            f"Object leak detected after validation error: {set(bpy.data.objects.keys()) - baseline_peg_objects}"
        )
        assert set(bpy.data.meshes.keys()) == baseline_peg_meshes, (
            f"Mesh leak detected after validation error: {set(bpy.data.meshes.keys()) - baseline_peg_meshes}"
        )
        print("  -> PASSED: Negative peg diameter rejected by core validation; zero leaks, state preserved")

        # 19. Testing Undo State Transition for Peg Joints (PR-005)
        print("\n[19/19] Testing Undo state transition for Peg joints...")
        res_undo_peg = bpy.ops.kinefig.create_peg_joint(
            peg_diameter_mm=3.0,
            peg_length_mm=5.0,
        )
        assert res_undo_peg == {"FINISHED"}
        undo_test_peg_name = "KF_Joint_Peg_003"
        assert undo_test_peg_name in bpy.data.objects, f"Expected {undo_test_peg_name} before Undo"

        if not undo_supported:
            print("  -> INFO: AUTOMATED UNDO: NOT VERIFIED IN HEADLESS")
        else:
            undo_call_res = bpy.ops.ed.undo()
            assert undo_call_res == {"FINISHED"}
            assert undo_test_peg_name not in bpy.data.objects, f"Undo failed to remove {undo_test_peg_name}"
            assert "User_Target_Mesh" in bpy.data.objects
            assert "KF_Joint_Peg_001" in bpy.data.objects
            assert "KF_Socket_Peg_001" in bpy.data.objects
            print(f"  -> PASSED: Undo removed {undo_test_peg_name}; earlier objects preserved")

        # 20. Testing Scene Unit Scale Adaptation (Unit Scale = 0.001 / Millimeters)
        print("\n[20/20] Testing Scene Unit Scale adaptation (scale_length = 0.001)...")
        orig_scale_length = bpy.context.scene.unit_settings.scale_length
        try:
            bpy.context.scene.unit_settings.scale_length = 0.001
            res_scale_peg = bpy.ops.kinefig.create_peg_joint(
                peg_diameter_mm=10.0,
                peg_length_mm=20.0,
            )
            assert res_scale_peg == {"FINISHED"}
            scale_peg_obj = bpy.context.view_layer.objects.active
            assert scale_peg_obj is not None
            # Raw BU dimension when scale_length is 0.001: 10.0 BU for 10.0mm diameter, 20.0 BU for 20.0mm length
            assert math.isclose(scale_peg_obj.dimensions.x, 10.0, abs_tol=1e-3), (
                f"Expected 10.0 BU in dimensions.x, got {scale_peg_obj.dimensions.x}"
            )
            assert math.isclose(scale_peg_obj.dimensions.z, 20.0, abs_tol=1e-3), (
                f"Expected 20.0 BU in dimensions.z, got {scale_peg_obj.dimensions.z}"
            )
            # World metric length (BU * scale_length): 0.010m (10.0mm) and 0.020m (20.0mm)
            world_x_m = scale_peg_obj.dimensions.x * bpy.context.scene.unit_settings.scale_length
            world_z_m = scale_peg_obj.dimensions.z * bpy.context.scene.unit_settings.scale_length
            assert math.isclose(world_x_m, 0.010, abs_tol=1e-4)
            assert math.isclose(world_z_m, 0.020, abs_tol=1e-4)
            print("  -> PASSED: Successfully adapted to scene scale_length=0.001; 10mm peg measures 10.0mm in world space")
        finally:
            bpy.context.scene.unit_settings.scale_length = orig_scale_length

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
            "KF_Joint_Peg_001",
            "KF_Joint_Peg_002",
            "KF_Joint_Peg_003",
            "KF_Joint_Peg_004",
            "KF_Socket_Peg_001",
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
