"""Joint operators for KineFig."""

import bpy
from ..geometry.joints import create_ball_joint_geometry
from ..core.errors import KineFigValidationError
from ..core.logging import log_error


class KINEFIG_OT_create_ball_joint(bpy.types.Operator):
    """Create a parametric male ball joint (sphere + cylindrical stem) as a single manifold mesh."""

    bl_idname = "kinefig.create_ball_joint"
    bl_label = "Create Ball Joint"
    bl_description = "Create a parametric male ball joint with manifold union and mm precision"
    bl_options = {"REGISTER", "UNDO"}

    ball_diameter_mm: bpy.props.FloatProperty(
        name="Ball Diameter (mm)",
        description="Diameter of the spherical ball in millimeters",
        default=5.0,
        min=0.1,
        max=100.0,
        precision=2,
    ) # type: ignore

    stem_diameter_mm: bpy.props.FloatProperty(
        name="Stem Diameter (mm)",
        description="Diameter of the cylindrical stem in millimeters",
        default=3.0,
        min=0.1,
        max=100.0,
        precision=2,
    ) # type: ignore

    stem_length_mm: bpy.props.FloatProperty(
        name="Stem Length (mm)",
        description="Length of the stem cylinder in millimeters",
        default=5.0,
        min=0.1,
        max=200.0,
        precision=2,
    ) # type: ignore

    segments: bpy.props.IntProperty(
        name="Segments",
        description="Radial resolution of sphere and cylinder",
        default=32,
        min=3,
        max=256,
    ) # type: ignore

    rings: bpy.props.IntProperty(
        name="Rings",
        description="Vertical ring resolution of the sphere",
        default=16,
        min=3,
        max=256,
    ) # type: ignore

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" if hasattr(context, "mode") else True

    def invoke(self, context, event):
        # Sync values from scene properties if available
        if hasattr(context, "scene") and hasattr(context.scene, "kinefig_ball_joint"):
            scene_props = context.scene.kinefig_ball_joint
            self.ball_diameter_mm = scene_props.ball_diameter_mm
            self.stem_diameter_mm = scene_props.stem_diameter_mm
            self.stem_length_mm = scene_props.stem_length_mm
            self.segments = scene_props.segments
            self.rings = scene_props.rings
        return self.execute(context)

    def execute(self, context):
        try:
            obj = create_ball_joint_geometry(
                context=context,
                ball_diameter_mm=self.ball_diameter_mm,
                stem_diameter_mm=self.stem_diameter_mm,
                stem_length_mm=self.stem_length_mm,
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

            self.report({"INFO"}, f"Created ball joint: {obj.name}")
            return {"FINISHED"}
        except KineFigValidationError as exc:
            self.report({"ERROR"}, str(exc))
            log_error(f"Validation failed: {exc}")
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Failed to create ball joint: {exc}")
            log_error(f"Failed to create ball joint", exc=exc)
            return {"CANCELLED"}
