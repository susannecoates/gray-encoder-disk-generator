"""Geometry utilities for optical encoder generation."""

from .arc_utils import (
    create_arc_points,
    create_sector_points,
    create_arc_sector,
    create_full_arc_disk,
    calculate_arc_length,
    calculate_sector_area,
    calculate_chord_length,
    validate_arc_parameters,
    optimize_segment_count,
    create_rounded_sector,
)

from .track_generator import TrackGenerator

from .assembly import EncoderAssembler

__all__ = [
    "create_arc_points",
    "create_sector_points",
    "create_arc_sector",
    "create_full_arc_disk",
    "calculate_arc_length",
    "calculate_sector_area",
    "calculate_chord_length",
    "validate_arc_parameters",
    "optimize_segment_count",
    "create_rounded_sector",
    "TrackGenerator",
    "EncoderAssembler",
]
