"""
Assembly module for combining all encoder disk components.

This module handles the final assembly of the encoder disk including
the base disk, track cutouts, limit switch bumpers, and any additional features.
"""

import math
from typing import Any, List, Tuple, Optional
from solid import union, difference, translate, rotate, cube, cylinder

from .arc_utils import create_full_arc_disk
from .track_generator import TrackGenerator


class EncoderAssembler:
    """Assembles complete encoder disk from individual components."""

    def __init__(self, params):
        """
        Initialize assembler.

        Args:
            params: EncoderParameters object
        """
        self.params = params
        self.track_generator = TrackGenerator(params)
        self.base_disk = None
        self.cutouts = None
        self.bumpers = []
        self.assembled_disk = None

    def create_base_disk(self) -> Any:
        """
        Create the base disk body.

        Returns:
            SolidPython object representing the base disk
        """
        # Create main disk as arc sector
        self.base_disk = create_full_arc_disk(
            self.params.radius_inner,
            self.params.radius_outer,
            self.params.arc_angle_deg,
            self.params.disk_thickness_mm,
        )

        return self.base_disk

    def create_limit_bumpers(self) -> List[Any]:
        """
        Create limit switch bumper objects.

        Returns:
            List of SolidPython bumper objects
        """
        self.bumpers.clear()

        # Create bumper at start position (0 degrees)
        start_bumper = self._create_single_bumper(0)
        self.bumpers.append(start_bumper)

        # Create bumper at end position
        end_bumper = self._create_single_bumper(self.params.arc_angle_deg)
        self.bumpers.append(end_bumper)

        return self.bumpers.copy()

    def _create_single_bumper(self, angle_deg: float) -> Any:
        """
        Create a single limit switch bumper at specified angle.

        Args:
            angle_deg: Angular position in degrees

        Returns:
            SolidPython bumper object
        """
        # Bumper dimensions
        bump_length = self.params.bump_extension_mm
        bump_width = (
            self.params.bump_width_deg * math.pi * self.params.radius_outer
        ) / 180
        bump_height = self.params.disk_thickness_mm

        # Create rectangular bumper
        bumper = cube([bump_length, bump_width, bump_height], center=True)

        # Position bumper at disk edge
        bump_center_radius = self.params.radius_outer + bump_length / 2

        # Calculate position
        angle_rad = math.radians(angle_deg)
        x_pos = bump_center_radius * math.cos(angle_rad)
        y_pos = bump_center_radius * math.sin(angle_rad)
        z_pos = bump_height / 2

        # Position and orient bumper
        positioned_bumper = translate([x_pos, y_pos, z_pos])(
            rotate(a=angle_deg, v=[0, 0, 1])(bumper)
        )

        return positioned_bumper

    def assemble_complete_disk(self, include_bumpers: bool = True) -> Any:
        """
        Assemble the complete encoder disk.

        Args:
            include_bumpers: Whether to include limit switch bumpers

        Returns:
            SolidPython object representing complete disk
        """
        # Create base components
        if self.base_disk is None:
            self.create_base_disk()

        # Generate track cutouts
        self.cutouts = self.track_generator.create_combined_cutouts()

        # Start with base disk
        components = [self.base_disk]

        # Add bumpers if requested
        if include_bumpers:
            if not self.bumpers:
                self.create_limit_bumpers()
            components.extend(self.bumpers)

        # Union all solid components
        solid_parts = union()(*components)

        # Apply cutouts if any exist
        if self.cutouts is not None:
            self.assembled_disk = difference()(solid_parts, self.cutouts)
        else:
            self.assembled_disk = solid_parts

        return self.assembled_disk

    def create_mounting_holes(
        self, hole_positions: List[Tuple[float, float]], hole_diameter: float = 3.0
    ) -> List[Any]:
        """
        Create additional mounting holes in the disk.

        Args:
            hole_positions: List of (x, y) positions for holes in mm
            hole_diameter: Diameter of mounting holes in mm

        Returns:
            List of SolidPython hole objects
        """
        holes = []
        hole_height = self.params.disk_thickness_mm + 2  # Ensure through-hole

        for x, y in hole_positions:
            hole = translate([x, y, -1])(cylinder(r=hole_diameter / 2, h=hole_height))
            holes.append(hole)

        return holes

    def add_mounting_holes(
        self, hole_positions: List[Tuple[float, float]], hole_diameter: float = 3.0
    ):
        """
        Add mounting holes to the assembled disk.

        Args:
            hole_positions: List of (x, y) positions for holes in mm
            hole_diameter: Diameter of mounting holes in mm
        """
        if self.assembled_disk is None:
            self.assemble_complete_disk()

        holes = self.create_mounting_holes(hole_positions, hole_diameter)
        if holes:
            hole_union = union()(*holes)
            self.assembled_disk = difference()(self.assembled_disk, hole_union)

    def create_calibration_marks(self) -> List[Any]:
        """
        Create calibration reference marks on the disk.

        Returns:
            List of SolidPython calibration mark objects
        """
        marks = []
        mark_depth = 0.2  # mm
        mark_width = 0.5  # mm
        mark_length = 5.0  # mm

        # Mark at 0 degrees
        zero_mark = translate(
            [
                self.params.radius_outer - mark_length / 2,
                0,
                self.params.disk_thickness_mm - mark_depth,
            ]
        )(cube([mark_length, mark_width, mark_depth], center=True))
        marks.append(zero_mark)

        # Mark at end angle
        end_angle_rad = math.radians(self.params.arc_angle_deg)
        end_x = (self.params.radius_outer - mark_length / 2) * math.cos(end_angle_rad)
        end_y = (self.params.radius_outer - mark_length / 2) * math.sin(end_angle_rad)

        end_mark = translate(
            [end_x, end_y, self.params.disk_thickness_mm - mark_depth]
        )(
            rotate(a=self.params.arc_angle_deg, v=[0, 0, 1])(
                cube([mark_length, mark_width, mark_depth], center=True)
            )
        )
        marks.append(end_mark)

        return marks

    def add_calibration_marks(self):
        """Add calibration marks to the assembled disk."""
        if self.assembled_disk is None:
            self.assemble_complete_disk()

        marks = self.create_calibration_marks()
        if marks:
            mark_union = union()(*marks)
            self.assembled_disk = difference()(self.assembled_disk, mark_union)

    def validate_assembly(self) -> Tuple[bool, List[str]]:
        """
        Validate the complete assembly for manufacturing issues.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate track spacing
        track_valid, track_errors = self.track_generator.validate_track_spacing()
        if not track_valid:
            errors.extend(track_errors)

        # Check bumper clearance
        if self.bumpers:
            bump_clearance = self._check_bumper_clearance()
            if not bump_clearance:
                errors.append("Bumpers may interfere with disk geometry")

        # Validate overall dimensions
        if self.params.outer_diameter_mm > 250:
            errors.append("Disk diameter may exceed typical 3D printer build volume")

        if self.params.disk_thickness_mm < 2:
            errors.append("Disk may be too thin for structural integrity")

        return len(errors) == 0, errors

    def _check_bumper_clearance(self) -> bool:
        """
        Check if bumpers have adequate clearance.

        Returns:
            True if clearance is adequate
        """
        # Simple check - ensure bumpers don't extend too far
        max_extension = self.params.radius_outer + self.params.bump_extension_mm

        # Arbitrary limit based on typical mounting constraints
        reasonable_limit = self.params.radius_outer * 1.2

        return max_extension <= reasonable_limit

    def get_assembly_info(self) -> dict:
        """
        Get comprehensive information about the assembled disk.

        Returns:
            Dictionary with assembly information
        """
        if not self.track_generator.track_patterns:
            self.track_generator.generate_all_tracks()

        feature_analysis = self.track_generator.calculate_feature_sizes()

        info = {
            "parameters": {
                "outer_diameter_mm": self.params.outer_diameter_mm,
                "inner_diameter_mm": self.params.inner_diameter_mm,
                "thickness_mm": self.params.disk_thickness_mm,
                "arc_angle_deg": self.params.arc_angle_deg,
                "num_positions": self.params.num_positions,
                "num_tracks": self.params.num_tracks,
            },
            "geometry": {
                "total_area_mm2": math.pi
                * (self.params.radius_outer**2 - self.params.radius_inner**2)
                * (self.params.arc_angle_deg / 360),
                "arc_length_outer_mm": (
                    self.params.arc_angle_deg * math.pi * self.params.radius_outer
                )
                / 180,
                "arc_length_inner_mm": (
                    self.params.arc_angle_deg * math.pi * self.params.radius_inner
                )
                / 180,
            },
            "encoding": {
                "angular_resolution_deg": self.params.angular_resolution_deg,
                "positions_per_degree": self.params.num_positions
                / self.params.arc_angle_deg,
                "encoding_efficiency": self.params.num_positions
                / (2**self.params.num_tracks),
            },
            "manufacturing": feature_analysis,
            "components": {
                "has_base_disk": self.base_disk is not None,
                "has_cutouts": self.cutouts is not None,
                "num_bumpers": len(self.bumpers),
                "is_assembled": self.assembled_disk is not None,
            },
        }

        return info
