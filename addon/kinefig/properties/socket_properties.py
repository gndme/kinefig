"""Property groups for KineFig socket parameters."""

import bpy


class KineFigBallSocketProperties(bpy.types.PropertyGroup):
    """Scene properties for creating parametric female ball socket cavities."""

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
        description="Distance from opening plane to deepest cavity point in millimeters",
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


class KineFigPegSocketProperties(bpy.types.PropertyGroup):
    """Scene properties for creating parametric female peg receiver cavities."""

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
        description="Distance from opening plane to deepest cavity point in millimeters",
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

