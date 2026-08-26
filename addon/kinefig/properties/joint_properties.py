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


class KineFigPegJointProperties(bpy.types.PropertyGroup):
    """Scene properties for creating parametric male peg connectors."""

    peg_diameter_mm: bpy.props.FloatProperty(
        name="Peg Diameter (mm)",
        description="Diameter of the cylindrical peg in millimeters",
        default=3.0,
        min=0.1,
        max=100.0,
        precision=2,
    )  # type: ignore

    peg_length_mm: bpy.props.FloatProperty(
        name="Peg Length (mm)",
        description="Length of the cylindrical peg in millimeters",
        default=5.0,
        min=0.1,
        max=200.0,
        precision=2,
    )  # type: ignore

    taper_angle_deg: bpy.props.FloatProperty(
        name="Taper Angle (°)",
        description="Draft/taper angle in degrees narrowing towards insertion tip (0 = straight cylinder)",
        default=0.0,
        min=0.0,
        max=89.0,
        precision=2,
    )  # type: ignore

    segments: bpy.props.IntProperty(
        name="Segments",
        description="Radial resolution of peg cylinder",
        default=32,
        min=3,
        max=256,
    )  # type: ignore

