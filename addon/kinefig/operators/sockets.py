"""Socket operators for KineFig."""

import bpy
from ..geometry.sockets import create_ball_socket_geometry, create_peg_socket_geometry
from ..core.errors import KineFigValidationError, KineFigGeometryError
from ..core.validation import require_positive
from ..core.logging import log_error, log_info, log_warning


class KINEFIG_OT_create_ball_socket(bpy.types.Operator):
    """Create a parametric female ball socket cavity tool as a watertight manifold mesh."""

    bl_idname = "kinefig.create_ball_socket"
    bl_label = "Create Ball Socket"
    bl_description = "Create a parametric female ball socket cavity tool with explicit radial clearance"
    bl_options = {"REGISTER", "UNDO"}

    ball_diameter_mm: bpy.props.FloatProperty(
        name="Ball Diameter (mm)",
        description="Diameter of the mating male ball in millimeters",
        default=5.0,
        min=0.1,
        max=100.0,
        precision=2,
    )  # type: ignore

    clearance_mm: bpy.props.FloatProperty(
        name="Clearance (mm)",
        description="Radial clearance between male ball and female cavity in millimeters",
        default=0.15,
        min=0.0,
        max=10.0,
        precision=3,
    )  # type: ignore

    socket_depth_mm: bpy.props.FloatProperty(
        name="Socket Depth (mm)",
        description="Distance from opening plane to deepest internal cavity point in millimeters",
        default=3.5,
        min=0.1,
        max=200.0,
        precision=2,
    )  # type: ignore

    segments: bpy.props.IntProperty(
        name="Segments",
        description="Radial resolution of socket sphere",
        default=32,
        min=3,
        max=256,
    )  # type: ignore

    rings: bpy.props.IntProperty(
        name="Rings",
        description="Vertical ring resolution of socket sphere",
        default=16,
        min=3,
        max=256,
    )  # type: ignore

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" if hasattr(context, "mode") else True

    def invoke(self, context, event):
        # Sync values from scene properties if available
        if hasattr(context, "scene") and hasattr(context.scene, "kinefig_ball_socket"):
            scene_props = context.scene.kinefig_ball_socket
            self.ball_diameter_mm = scene_props.ball_diameter_mm
            self.clearance_mm = scene_props.clearance_mm
            self.socket_depth_mm = scene_props.socket_depth_mm
            self.segments = scene_props.segments
            self.rings = scene_props.rings
        return self.execute(context)

    def execute(self, context):
        try:
            obj = create_ball_socket_geometry(
                context=context,
                ball_diameter_mm=self.ball_diameter_mm,
                clearance_mm=self.clearance_mm,
                socket_depth_mm=self.socket_depth_mm,
                segments=self.segments,
                rings=self.rings,
            )

            # Set as active and selected in 3D Viewport
            if hasattr(context, "view_layer") and hasattr(context.view_layer, "objects"):
                for o in context.view_layer.objects:
                    if hasattr(o, "select_set"):
                        o.select_set(False)
                if hasattr(obj, "select_set"):
                    obj.select_set(True)
                context.view_layer.objects.active = obj

            self.report({"INFO"}, f"Created ball socket: {obj.name}")
            return {"FINISHED"}
        except KineFigValidationError as exc:
            self.report({"ERROR"}, f"Validation error: {exc}")
            log_error(f"Validation failed: {exc}")
            return {"CANCELLED"}
        except KineFigGeometryError as exc:
            self.report({"ERROR"}, f"Geometry error: {exc}")
            log_error(f"Geometry operation failed: {exc}")
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to create ball socket: {exc}")
            log_error("Failed to create ball socket", exc=exc)
            return {"CANCELLED"}


class KINEFIG_OT_use_selected_ball(bpy.types.Operator):
    """Copy ball diameter from selected KineFig Ball Joint into socket settings."""

    bl_idname = "kinefig.use_selected_ball"
    bl_label = "Use Selected Ball"
    bl_description = "Read ball diameter from selected KineFig Ball Joint to match socket"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        try:
            obj = getattr(context, "active_object", None)
            if obj is None:
                return False
            return (
                obj.get("kf_type") == "joint"
                and obj.get("kf_joint_type") == "ball"
                and "kf_ball_diameter_mm" in obj
            )
        except Exception:
            return False

    def execute(self, context):
        obj = getattr(context, "active_object", None)
        if not obj or obj.get("kf_type") != "joint" or obj.get("kf_joint_type") != "ball":
            self.report({"WARNING"}, "Active object is not a KineFig Ball Joint")
            return {"CANCELLED"}

        ball_d_raw = obj.get("kf_ball_diameter_mm")
        if ball_d_raw is None:
            self.report({"WARNING"}, f"Selected ball joint {obj.name} has no kf_ball_diameter_mm metadata")
            log_warning(f"Selected ball joint {obj.name} has no kf_ball_diameter_mm metadata")
            return {"CANCELLED"}

        try:
            val = require_positive(ball_d_raw, "kf_ball_diameter_mm")
        except (KineFigValidationError, Exception) as exc:
            self.report({"WARNING"}, f"Invalid ball diameter metadata on {obj.name}: {exc}")
            log_warning(f"Failed to use selected ball metadata from {obj.name}: {exc}")
            return {"CANCELLED"}

        if hasattr(context, "scene") and hasattr(context.scene, "kinefig_ball_socket"):
            context.scene.kinefig_ball_socket.ball_diameter_mm = val

        self.report({"INFO"}, f"Loaded ball diameter {val:.2f} mm from {obj.name}")
        log_info(f"Loaded ball diameter {val:.2f} mm from {obj.name}")
        return {"FINISHED"}


class KINEFIG_OT_create_peg_socket(bpy.types.Operator):
    """Create a parametric female peg receiver socket cavity tool as a watertight manifold mesh."""

    bl_idname = "kinefig.create_peg_socket"
    bl_label = "Create Peg Socket"
    bl_description = "Create a parametric female peg receiver socket cavity tool with explicit radial clearance"
    bl_options = {"REGISTER", "UNDO"}

    peg_diameter_mm: bpy.props.FloatProperty(
        name="Peg Diameter (mm)",
        description="Diameter of the mating male peg in millimeters",
        default=3.0,
        min=0.1,
        max=100.0,
        precision=2,
    )  # type: ignore

    radial_clearance_mm: bpy.props.FloatProperty(
        name="Clearance (mm)",
        description="Radial clearance between male peg and female cavity in millimeters",
        default=0.15,
        min=0.0,
        max=10.0,
        precision=3,
    )  # type: ignore

    socket_depth_mm: bpy.props.FloatProperty(
        name="Socket Depth (mm)",
        description="Distance from opening plane to deepest internal cavity point in millimeters",
        default=5.0,
        min=0.1,
        max=200.0,
        precision=2,
    )  # type: ignore

    segments: bpy.props.IntProperty(
        name="Segments",
        description="Radial resolution of socket cavity",
        default=32,
        min=3,
        max=256,
    )  # type: ignore

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" if hasattr(context, "mode") else True

    def invoke(self, context, event):
        # Sync values from scene properties if available
        if hasattr(context, "scene") and hasattr(context.scene, "kinefig_peg_socket"):
            scene_props = context.scene.kinefig_peg_socket
            self.peg_diameter_mm = scene_props.peg_diameter_mm
            self.radial_clearance_mm = scene_props.radial_clearance_mm
            self.socket_depth_mm = scene_props.socket_depth_mm
            self.segments = scene_props.segments
        return self.execute(context)

    def execute(self, context):
        try:
            obj = create_peg_socket_geometry(
                context=context,
                peg_diameter_mm=self.peg_diameter_mm,
                radial_clearance_mm=self.radial_clearance_mm,
                socket_depth_mm=self.socket_depth_mm,
                segments=self.segments,
            )

            # Set as active and selected in 3D Viewport
            if hasattr(context, "view_layer") and hasattr(context.view_layer, "objects"):
                for o in context.view_layer.objects:
                    if hasattr(o, "select_set"):
                        o.select_set(False)
                if hasattr(obj, "select_set"):
                    obj.select_set(True)
                context.view_layer.objects.active = obj

            self.report({"INFO"}, f"Created peg socket: {obj.name}")
            return {"FINISHED"}
        except KineFigValidationError as exc:
            self.report({"ERROR"}, f"Validation error: {exc}")
            log_error(f"Validation failed: {exc}")
            return {"CANCELLED"}
        except KineFigGeometryError as exc:
            self.report({"ERROR"}, f"Geometry error: {exc}")
            log_error(f"Geometry operation failed: {exc}")
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to create peg socket: {exc}")
            log_error("Failed to create peg socket", exc=exc)
            return {"CANCELLED"}


class KINEFIG_OT_use_selected_peg(bpy.types.Operator):
    """Copy peg diameter from selected KineFig Peg Joint into socket settings."""

    bl_idname = "kinefig.use_selected_peg"
    bl_label = "Use Selected Peg"
    bl_description = "Read peg diameter from selected KineFig Peg Joint to match socket"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        try:
            obj = getattr(context, "active_object", None)
            if obj is None:
                return False
            return (
                obj.get("kf_type") == "joint"
                and obj.get("kf_joint_type") == "peg"
                and "kf_peg_diameter_mm" in obj
            )
        except Exception:
            return False

    def execute(self, context):
        obj = getattr(context, "active_object", None)
        if not obj or obj.get("kf_type") != "joint" or obj.get("kf_joint_type") != "peg":
            self.report({"WARNING"}, "Active object is not a KineFig Peg Joint")
            return {"CANCELLED"}

        peg_d_raw = obj.get("kf_peg_diameter_mm")
        if peg_d_raw is None:
            self.report({"WARNING"}, f"Selected peg joint {obj.name} has no kf_peg_diameter_mm metadata")
            log_warning(f"Selected peg joint {obj.name} has no kf_peg_diameter_mm metadata")
            return {"CANCELLED"}

        try:
            val = require_positive(peg_d_raw, "kf_peg_diameter_mm")
        except (KineFigValidationError, Exception) as exc:
            self.report({"WARNING"}, f"Invalid peg diameter metadata on {obj.name}: {exc}")
            log_warning(f"Failed to use selected peg metadata from {obj.name}: {exc}")
            return {"CANCELLED"}

        if hasattr(context, "scene") and hasattr(context.scene, "kinefig_peg_socket"):
            context.scene.kinefig_peg_socket.peg_diameter_mm = val

        self.report({"INFO"}, f"Loaded peg diameter {val:.2f} mm from {obj.name}")
        log_info(f"Loaded peg diameter {val:.2f} mm from {obj.name}")
        return {"FINISHED"}

