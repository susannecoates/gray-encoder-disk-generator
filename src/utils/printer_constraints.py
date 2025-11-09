"""
3D Printing constraints and validation utilities.

This module contains functions to validate designs against 3D printing
limitations and provide recommendations for optimal printing.
"""

from typing import List, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class PrinterConstraints:
    """3D printer physical and quality constraints."""

    # Nozzle and extrusion
    nozzle_diameter_mm: float = 0.4
    layer_height_mm: float = 0.2
    line_width_mm: float = 0.4

    # Minimum feature sizes
    min_wall_thickness_mm: float = 1.2  # 3 perimeters
    min_gap_width_mm: float = 0.5  # Reliable gap printing
    min_hole_diameter_mm: float = 1.0  # Minimum printable hole

    # Geometric limitations
    max_overhang_angle_deg: float = 45  # Without supports
    max_bridge_distance_mm: float = 5.0  # Unsupported bridging
    min_support_distance_mm: float = 0.2  # Support gap

    # Material properties
    shrinkage_factor: float = 0.002  # Typical PLA shrinkage
    thermal_expansion_ppm: float = 70  # Per degree C

    # Quality settings
    perimeter_count: int = 3
    infill_percentage: float = 20
    top_bottom_layers: int = 3


class PrintabilityAnalyzer:
    """Analyzes encoder designs for 3D printing feasibility."""

    def __init__(self, constraints: PrinterConstraints = None):
        self.constraints = constraints or PrinterConstraints()
        self.issues: List[str] = []
        self.recommendations: List[str] = []

    def analyze_encoder_design(self, params) -> Tuple[bool, List[str], List[str]]:
        """
        Analyze encoder design for printability.

        Args:
            params: EncoderParameters object

        Returns:
            Tuple of (is_printable, issues, recommendations)
        """
        self.issues.clear()
        self.recommendations.clear()

        self._check_wall_thickness(params)
        self._check_gap_sizes(params)
        self._check_feature_sizes(params)
        self._check_overhang_requirements(params)
        self._check_bridging_requirements(params)
        self._generate_print_recommendations(params)

        return len(self.issues) == 0, self.issues.copy(), self.recommendations.copy()

    def _check_wall_thickness(self, params):
        """Check if walls meet minimum thickness requirements."""
        if params.track_width_mm < self.constraints.min_wall_thickness_mm:
            self.issues.append(
                f"Track width {params.track_width_mm}mm less than minimum "
                f"wall thickness {self.constraints.min_wall_thickness_mm}mm"
            )

        if params.disk_thickness_mm < self.constraints.layer_height_mm * 3:
            self.issues.append(
                f"Disk thickness {params.disk_thickness_mm}mm should be at least "
                f"{self.constraints.layer_height_mm * 3}mm (3 layers minimum)"
            )

    def _check_gap_sizes(self, params):
        """Check if gaps can be printed reliably."""
        import math

        # Calculate gap size at different radii
        for track_idx in range(params.num_tracks):
            track_radius = (
                params.radius_inner
                + track_idx * (params.track_width_mm + params.track_spacing_mm)
                + params.track_width_mm / 2
            )

            gap_size_mm = (params.gap_width_deg * math.pi * track_radius) / 180

            if gap_size_mm < self.constraints.min_gap_width_mm:
                self.issues.append(
                    f"Gap size {gap_size_mm:.2f}mm at track {track_idx + 1} "
                    f"less than minimum {self.constraints.min_gap_width_mm}mm"
                )

    def _check_feature_sizes(self, params):
        """Check minimum feature size compliance."""
        if params.track_spacing_mm < self.constraints.nozzle_diameter_mm:
            self.issues.append(
                f"Track spacing {params.track_spacing_mm}mm less than "
                f"nozzle diameter {self.constraints.nozzle_diameter_mm}mm"
            )

        if params.inner_diameter_mm < self.constraints.min_hole_diameter_mm:
            self.issues.append(
                f"Inner diameter {params.inner_diameter_mm}mm less than "
                f"minimum hole diameter {self.constraints.min_hole_diameter_mm}mm"
            )

    def _check_overhang_requirements(self, params):
        """Check for problematic overhangs."""
        # Bumpers create overhangs - check if they're printable
        bump_overhang_ratio = params.bump_extension_mm / params.disk_thickness_mm

        if bump_overhang_ratio > 1.0:
            self.recommendations.append(
                "Bumper extension may require supports for reliable printing"
            )

        # Check if cutouts create overhangs
        if params.disk_thickness_mm > 2 * self.constraints.layer_height_mm:
            self.recommendations.append(
                "Consider printing with cutouts facing up to avoid overhangs"
            )

    def _check_bridging_requirements(self, params):
        """Check for bridges that may fail."""
        import math

        # Calculate maximum bridge distance in cutouts
        max_gap_size_mm = (params.gap_width_deg * math.pi * params.radius_outer) / 180

        if max_gap_size_mm > self.constraints.max_bridge_distance_mm:
            self.recommendations.append(
                f"Large gaps ({max_gap_size_mm:.1f}mm) may need slower print speeds"
            )

    def _generate_print_recommendations(self, params):
        """Generate printing recommendations."""
        self.recommendations.extend(
            [
                "Print with cutouts facing down for best edge quality",
                "Use 0.2mm layer height for good detail resolution",
                f"Set perimeter count to {self.constraints.perimeter_count} "
                f"for strength",
                "Consider PETG or ASA for marine environment UV resistance",
                "Print at 50-60mm/s for fine details, 100mm/s for infill",
            ]
        )

        # Material-specific recommendations
        if params.outer_diameter_mm > 100:
            self.recommendations.append(
                "Large disk may require heated bed and enclosure to prevent warping"
            )

        if params.num_tracks > 5:
            self.recommendations.append(
                "High track count requires excellent printer calibration"
            )


def estimate_print_time(
    params, constraints: PrinterConstraints = None
) -> Dict[str, float]:
    """
    Estimate print time for encoder disk.

    Args:
        params: EncoderParameters object
        constraints: PrinterConstraints object

    Returns:
        Dictionary with time estimates in minutes
    """
    import math

    if constraints is None:
        constraints = PrinterConstraints()

    # Calculate volume and surface area
    disk_volume = (
        math.pi
        * (params.radius_outer**2 - params.radius_inner**2)
        * params.disk_thickness_mm
    )

    # Estimate based on typical print speeds
    perimeter_speed_mm_min = 50 * 60  # 50mm/s
    infill_speed_mm_min = 100 * 60  # 100mm/s

    # Rough estimates
    layer_count = params.disk_thickness_mm / constraints.layer_height_mm
    perimeter_time = layer_count * 2  # 2 minutes per layer for perimeters
    infill_time = disk_volume / 1000 * 0.5  # 0.5 min per cm³

    total_time = perimeter_time + infill_time

    return {
        "total_minutes": total_time,
        "perimeter_minutes": perimeter_time,
        "infill_minutes": infill_time,
        "layer_count": layer_count,
    }


def generate_slicer_settings(
    params, constraints: PrinterConstraints = None
) -> Dict[str, Any]:
    """
    Generate recommended slicer settings for the encoder disk.

    Args:
        params: EncoderParameters object
        constraints: PrinterConstraints object

    Returns:
        Dictionary of recommended slicer settings
    """
    if constraints is None:
        constraints = PrinterConstraints()

    return {
        "layer_height": constraints.layer_height_mm,
        "line_width": constraints.line_width_mm,
        "perimeters": constraints.perimeter_count,
        "top_solid_layers": constraints.top_bottom_layers,
        "bottom_solid_layers": constraints.top_bottom_layers,
        "infill_percentage": constraints.infill_percentage,
        "print_speed_perimeter": 50,  # mm/s
        "print_speed_infill": 100,  # mm/s
        "print_speed_first_layer": 20,  # mm/s
        "bed_temperature": 60,  # °C for PLA
        "extruder_temperature": 210,  # °C for PLA
        "cooling_fan": True,
        "supports": False,  # Design should not need supports
        "brim_width": 5,  # mm for bed adhesion
        "retraction_distance": 1.0,  # mm
        "retraction_speed": 30,  # mm/s
    }
