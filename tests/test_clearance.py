"""Unit tests for clearance mathematics and socket dimensions."""

import math
import pytest
from addon.kinefig.core.clearance import (
    compute_socket_diameter,
    compute_socket_radius,
    compute_opening_diameter,
)


def test_compute_socket_diameter_examples():
    """Verify radial clearance contract: socket_diameter = ball_diameter + 2 * clearance."""
    # Zero clearance: line-to-line fit
    assert compute_socket_diameter(5.0, 0.0) == 5.0

    # Default radial clearance 0.15 mm
    assert math.isclose(compute_socket_diameter(5.0, 0.15), 5.30, abs_tol=1e-6)

    # 6.0 mm ball with 0.2 mm clearance
    assert math.isclose(compute_socket_diameter(6.0, 0.2), 6.40, abs_tol=1e-6)

    # Small 3.0 mm wrist ball with 0.1 mm clearance
    assert math.isclose(compute_socket_diameter(3.0, 0.1), 3.20, abs_tol=1e-6)


def test_compute_socket_radius():
    """Verify socket cavity radius = (ball_diameter / 2) + clearance."""
    assert math.isclose(compute_socket_radius(5.0, 0.15), 2.65, abs_tol=1e-6)
    assert math.isclose(compute_socket_radius(6.0, 0.2), 3.20, abs_tol=1e-6)


def test_compute_opening_diameter():
    """Verify opening diameter calculation at insertion plane z = 0."""
    # Hemisphere socket: depth == radius -> opening diameter == socket diameter
    socket_d = 5.30
    depth_hemi = 2.65
    assert math.isclose(compute_opening_diameter(socket_d, depth_hemi), 5.30, abs_tol=1e-6)

    # Retaining socket: depth 3.5 mm, diameter 5.3 mm
    # opening_radius = sqrt(3.5 * (5.3 - 3.5)) = sqrt(6.3) ≈ 2.50998
    # opening_diameter ≈ 5.01996
    expected_open_d = 2.0 * math.sqrt(3.5 * (5.3 - 3.5))
    assert math.isclose(compute_opening_diameter(5.3, 3.5), expected_open_d, abs_tol=1e-6)

    # Shallow socket: depth 1.0 mm, diameter 5.3 mm
    expected_shallow_d = 2.0 * math.sqrt(1.0 * (5.3 - 1.0))
    assert math.isclose(compute_opening_diameter(5.3, 1.0), expected_shallow_d, abs_tol=1e-6)

    # Invalid / boundary depths return 0.0
    assert compute_opening_diameter(5.3, 0.0) == 0.0
    assert compute_opening_diameter(5.3, -1.0) == 0.0
    assert compute_opening_diameter(5.3, 5.3) == 0.0
    assert compute_opening_diameter(5.3, 6.0) == 0.0
