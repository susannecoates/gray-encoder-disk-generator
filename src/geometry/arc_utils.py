"""
Arc and sector geometry utilities for encoder disk generation.

This module provides functions to create arc segments, sectors, and other
geometric primitives required for optical encoder disk construction.
"""

import math
from typing import List, Tuple
from solid import polygon, linear_extrude


def create_arc_points(
    radius: float, start_deg: float, end_deg: float, segments: int = 50
) -> List[Tuple[float, float]]:
    """
    Generate points along an arc.

    Args:
        radius: Arc radius in mm
        start_deg: Start angle in degrees
        end_deg: End angle in degrees
        segments: Number of segments for smoothness

    Returns:
        List of (x, y) coordinate tuples
    """
    points = []
    start_rad = math.radians(start_deg)
    end_rad = math.radians(end_deg)

    for i in range(segments + 1):
        angle = start_rad + (end_rad - start_rad) * i / segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        points.append((x, y))

    return points


def create_sector_points(
    inner_radius: float,
    outer_radius: float,
    start_deg: float,
    end_deg: float,
    segments: int = 50,
) -> List[Tuple[float, float]]:
    """
    Generate points for an annular sector (ring segment).

    Args:
        inner_radius: Inner radius in mm
        outer_radius: Outer radius in mm
        start_deg: Start angle in degrees
        end_deg: End angle in degrees
        segments: Number of segments for arc smoothness

    Returns:
        List of (x, y) coordinate tuples forming a closed polygon
    """
    points = []

    # Outer arc (counter-clockwise)
    outer_points = create_arc_points(outer_radius, start_deg, end_deg, segments)
    points.extend(outer_points)

    # Inner arc (clockwise - reversed)
    inner_points = create_arc_points(inner_radius, start_deg, end_deg, segments)
    points.extend(reversed(inner_points))

    return points


def create_arc_sector(
    inner_radius: float,
    outer_radius: float,
    start_deg: float,
    end_deg: float,
    height: float,
    segments: int = 50,
):
    """
    Create a 3D arc sector using SolidPython.

    Args:
        inner_radius: Inner radius in mm
        outer_radius: Outer radius in mm
        start_deg: Start angle in degrees
        end_deg: End angle in degrees
        height: Extrusion height in mm
        segments: Number of segments for smoothness

    Returns:
        SolidPython 3D object
    """
    points = create_sector_points(
        inner_radius, outer_radius, start_deg, end_deg, segments
    )
    # Convert to list of lists for SolidPython polygon()
    point_lists = [[p[0], p[1]] for p in points]
    return linear_extrude(height=height)(polygon(point_lists))


def create_full_arc_disk(
    inner_radius: float,
    outer_radius: float,
    arc_angle_deg: float,
    thickness: float,
    segments: int = 50,
):
    """
    Create the main disk body as an arc sector.

    Args:
        inner_radius: Inner radius (mounting hole) in mm
        outer_radius: Outer radius in mm
        arc_angle_deg: Total arc angle in degrees
        thickness: Disk thickness in mm
        segments: Number of segments for smoothness

    Returns:
        SolidPython 3D object representing the disk body
    """
    return create_arc_sector(
        inner_radius, outer_radius, 0, arc_angle_deg, thickness, segments
    )


def calculate_arc_length(radius: float, angle_deg: float) -> float:
    """
    Calculate arc length for given radius and angle.

    Args:
        radius: Arc radius in mm
        angle_deg: Arc angle in degrees

    Returns:
        Arc length in mm
    """
    return (angle_deg * math.pi * radius) / 180


def calculate_sector_area(
    inner_radius: float, outer_radius: float, angle_deg: float
) -> float:
    """
    Calculate area of an annular sector.

    Args:
        inner_radius: Inner radius in mm
        outer_radius: Outer radius in mm
        angle_deg: Sector angle in degrees

    Returns:
        Sector area in mm²
    """
    angle_rad = math.radians(angle_deg)
    outer_area = 0.5 * outer_radius**2 * angle_rad
    inner_area = 0.5 * inner_radius**2 * angle_rad
    return outer_area - inner_area


def calculate_chord_length(radius: float, angle_deg: float) -> float:
    """
    Calculate chord length for given radius and angle.

    Args:
        radius: Arc radius in mm
        angle_deg: Arc angle in degrees

    Returns:
        Chord length in mm
    """
    return 2 * radius * math.sin(math.radians(angle_deg) / 2)


def validate_arc_parameters(
    inner_radius: float, outer_radius: float, start_deg: float, end_deg: float
) -> Tuple[bool, List[str]]:
    """
    Validate arc geometry parameters.

    Args:
        inner_radius: Inner radius in mm
        outer_radius: Outer radius in mm
        start_deg: Start angle in degrees
        end_deg: End angle in degrees

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if inner_radius < 0:
        errors.append("Inner radius cannot be negative")

    if outer_radius <= inner_radius:
        errors.append("Outer radius must be greater than inner radius")

    if start_deg < 0 or start_deg >= 360:
        errors.append("Start angle must be between 0 and 360 degrees")

    if end_deg <= start_deg:
        errors.append("End angle must be greater than start angle")

    if (end_deg - start_deg) > 360:
        errors.append("Arc span cannot exceed 360 degrees")

    return len(errors) == 0, errors


def optimize_segment_count(
    radius: float, angle_deg: float, max_chord_error_mm: float = 0.1
) -> int:
    """
    Calculate optimal number of segments for given chord error tolerance.

    Args:
        radius: Arc radius in mm
        angle_deg: Arc angle in degrees
        max_chord_error_mm: Maximum allowable chord approximation error in mm

    Returns:
        Recommended number of segments
    """
    if angle_deg <= 0 or radius <= 0:
        return 10  # Minimum reasonable count

    # Calculate error for single segment
    single_segment_angle = math.radians(angle_deg)
    chord_error = radius * (1 - math.cos(single_segment_angle / 2))

    if chord_error <= max_chord_error_mm:
        return 1

    # Calculate segments needed
    # Error per segment = radius * (1 - cos(θ/2)) where θ = angle_per_segment
    # Solve for number of segments
    angle_per_segment = 2 * math.acos(1 - max_chord_error_mm / radius)
    segments = math.ceil(math.radians(angle_deg) / angle_per_segment)

    # Practical limits
    return max(3, min(segments, 200))


def create_rounded_sector(
    inner_radius: float,
    outer_radius: float,
    start_deg: float,
    end_deg: float,
    height: float,
    corner_radius: float = 0.5,
    segments: int = 50,
):
    """
    Create an arc sector with rounded corners for better printing.

    Args:
        inner_radius: Inner radius in mm
        outer_radius: Outer radius in mm
        start_deg: Start angle in degrees
        end_deg: End angle in degrees
        height: Extrusion height in mm
        corner_radius: Radius for corner rounding in mm
        segments: Number of segments for smoothness

    Returns:
        SolidPython 3D object with rounded corners
    """
    # For now, return regular sector
    # TODO: Implement corner rounding using offset() operations
    return create_arc_sector(
        inner_radius, outer_radius, start_deg, end_deg, height, segments
    )
