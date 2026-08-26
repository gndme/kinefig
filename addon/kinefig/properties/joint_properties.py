"""Property groups for KineFig joint parameters."""

import bpy


class KineFigBallJointProperties(bpy.types.PropertyGroup):
    """Scene properties for creating parametric male ball joints."""

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
        description="Diameter of the cylindrical stem in millimeters (must be less than ball diameter)",
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


class KineFigDoubleBallJointProperties(bpy.types.PropertyGroup):
    """Scene properties for creating parametric double ball (dumbbell) joints."""

    ball_a_diameter_mm: bpy.props.FloatProperty(
        name="Ball A Diameter (mm)",
        description="Diameter of Ball A in millimeters (centered at origin)",
        default=5.0,
        min=0.1,
        max=100.0,
        precision=2,
    )  # type: ignore

    ball_b_diameter_mm: bpy.props.FloatProperty(
        name="Ball B Diameter (mm)",
        description="Diameter of Ball B in millimeters (centered at center distance along +Z)",
        default=5.0,
        min=0.1,
        max=100.0,
        precision=2,
    )  # type: ignore

    stem_diameter_mm: bpy.props.FloatProperty(
        name="Stem Diameter (mm)",
        description="Diameter of the connecting neck stem in millimeters (must be less than both balls)",
        default=3.0,
        min=0.1,
        max=100.0,
        precision=2,
    )  # type: ignore

    center_distance_mm: bpy.props.FloatProperty(
        name="Center Distance (mm)",
        description="Distance between Ball A center and Ball B center along local +Z axis (must be >= (Ball A + Ball B) / 2 to preserve distinct ball lobes)",
        default=8.0,
        min=0.1,
        max=200.0,
        precision=2,
    )  # type: ignore

    segments: bpy.props.IntProperty(
        name="Segments",
        description="Radial resolution of spheres and stem cylinder",
        default=32,
        min=3,
        max=256,
    )  # type: ignore

    rings: bpy.props.IntProperty(
        name="Rings",
        description="Vertical ring resolution of spheres",
        default=16,
        min=3,
        max=256,
    )  # type: ignore

