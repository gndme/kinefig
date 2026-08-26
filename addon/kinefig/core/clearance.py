"""Clearance mathematics and joint-fit calculations for KineFig."""

import math


def compute_socket_diameter(ball_diameter_mm: float, clearance_mm: float) -> float:
    """Calculate nominal female socket cavity diameter from male ball diameter and radial clearance.

    Clearance Contract:
    Clearance is defined as radial clearance (applied uniformly on all sides
    between the male ball surface and female cavity surface).
    Therefore:
        cavity_radius = ball_radius + clearance
        cavity_diameter = ball_diameter + 2 * clearance

    Args:
        ball_diameter_mm: Diameter of the mating male ball in mm (> 0).
        clearance_mm: Radial clearance in mm (>= 0).

    Returns:
        Internal socket cavity diameter in mm.
    """
    return float(ball_diameter_mm) + 2.0 * float(clearance_mm)


def compute_socket_radius(ball_diameter_mm: float, clearance_mm: float) -> float:
    """Calculate nominal socket cavity radius from male ball diameter and radial clearance."""
    return (float(ball_diameter_mm) / 2.0) + float(clearance_mm)


def compute_opening_diameter(socket_diameter_mm: float, socket_depth_mm: float) -> float:
    """Calculate the circular opening diameter at the insertion plane z = 0.

    For a spherical cavity whose deepest point is at z = socket_depth and whose
    opening plane is at z = 0:
        center_z = socket_depth - radius
        opening_radius = sqrt(radius^2 - center_z^2)
                       = sqrt(socket_depth * (socket_diameter - socket_depth))
        opening_diameter = 2 * opening_radius

    Args:
        socket_diameter_mm: Internal cavity diameter in mm.
        socket_depth_mm: Distance from opening plane to deepest cavity point in mm.

    Returns:
        Opening diameter at z = 0 in mm (0.0 if depth is outside (0, diameter)).
    """
    if socket_depth_mm <= 0.0 or socket_depth_mm >= socket_diameter_mm:
        return 0.0
    val = socket_depth_mm * (socket_diameter_mm - socket_depth_mm)
    return 2.0 * math.sqrt(max(0.0, val))
