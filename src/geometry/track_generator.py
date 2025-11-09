"""
Track pattern generator for Gray code optical encoder disks.

This module generates the cutout patterns for each track based on Gray code
encoding and validates them against manufacturing constraints.
"""

import math
from typing import List, Dict, Any, Tuple
from solid import union, difference

from gray_code import extract_track_pattern, gray_code_bits
from .arc_utils import create_arc_sector


class TrackGenerator:
    """Generates track patterns for Gray code encoder disks."""

    def __init__(self, params):
        """
        Initialize track generator.

        Args:
            params: EncoderParameters object
        """
        self.params = params
        self.track_patterns = []
        self.cutout_objects = []

    def generate_all_tracks(self) -> List[List[int]]:
        """
        Generate Gray code patterns for all tracks.

        Returns:
            List of track patterns, where each pattern is a list of 0/1 values
        """
        self.track_patterns.clear()

        for track_idx in range(self.params.num_tracks):
            pattern = extract_track_pattern(
                track_idx, self.params.num_positions, self.params.num_tracks
            )
            self.track_patterns.append(pattern)

        return self.track_patterns.copy()

    def generate_track_cutouts(self, track_idx: int) -> List[Any]:
        """
        Generate 3D cutout objects for a specific track.

        Args:
            track_idx: Index of track (0 = outermost/LSB, n-1 = innermost/MSB)

        Returns:
            List of SolidPython objects representing cutouts
        """
        if track_idx >= len(self.track_patterns):
            raise ValueError(f"Track {track_idx} not generated yet")

        pattern = self.track_patterns[track_idx]
        cutouts = []

        # Calculate track radii - tracks start from outer edge and work inward
        # Track 0 = outermost track (LSB, maximum radius, most frequent changes)
        # Track N-1 = innermost track (MSB, minimum radius, least frequent changes)
        track_outer_radius = (
            self.params.radius_outer - track_idx * self.params.track_pitch_mm
        )
        track_inner_radius = track_outer_radius - self.params.track_width_mm

        # Validate track doesn't extend below inner radius
        if track_inner_radius < self.params.radius_inner:
            raise ValueError(
                f"Track {track_idx} extends below inner radius "
                f"({track_inner_radius:.2f}mm < {self.params.radius_inner:.2f}mm). "
                f"Reduce number of tracks or adjust spacing."
            )

        # Generate cutouts for each '1' bit in the pattern
        # For transmissive encoders: '1' = light passes through = cutout/open
        #                           '0' = light blocked = solid material
        current_run_start = None
        current_run_length = 0

        for pos_idx, bit_value in enumerate(pattern):
            if bit_value == 1:  # Start or continue a cutout run
                if current_run_start is None:
                    current_run_start = pos_idx
                current_run_length += 1
            else:  # End of cutout run
                if current_run_start is not None:
                    cutout = self._create_position_cutout(
                        track_inner_radius,
                        track_outer_radius,
                        current_run_start,
                        current_run_length,
                    )
                    cutouts.append(cutout)
                    current_run_start = None
                    current_run_length = 0

        # Handle cutout run that ends at the last position
        if current_run_start is not None:
            cutout = self._create_position_cutout(
                track_inner_radius,
                track_outer_radius,
                current_run_start,
                current_run_length,
            )
            cutouts.append(cutout)

        return cutouts

    def _create_position_cutout(
        self, inner_radius: float, outer_radius: float, start_position: int, length: int
    ) -> Any:
        """
        Create a cutout for a run of consecutive positions.

        Args:
            inner_radius: Inner radius of track in mm
            outer_radius: Outer radius of track in mm
            start_position: Starting position index
            length: Number of consecutive positions

        Returns:
            SolidPython cutout object
        """
        # Calculate angular span
        position_angle_deg = self.params.arc_angle_deg / self.params.num_positions
        start_angle_deg = start_position * position_angle_deg
        end_angle_deg = start_angle_deg + (length * position_angle_deg)

        # Add small overlap to ensure clean cuts
        overlap_deg = 0.1
        start_angle_deg -= overlap_deg
        end_angle_deg += overlap_deg

        # Create cutout with extra height to ensure complete cut-through
        height = self.params.disk_thickness_mm + 2

        return create_arc_sector(
            inner_radius, outer_radius, start_angle_deg, end_angle_deg, height
        )

    def generate_all_cutouts(self) -> List[Any]:
        """
        Generate all cutout objects for all tracks.

        Returns:
            List of all SolidPython cutout objects
        """
        self.cutout_objects.clear()

        if not self.track_patterns:
            self.generate_all_tracks()

        for track_idx in range(self.params.num_tracks):
            track_cutouts = self.generate_track_cutouts(track_idx)
            self.cutout_objects.extend(track_cutouts)

        return self.cutout_objects.copy()

    def create_combined_cutouts(self) -> Any:
        """
        Combine all cutouts into a single union object.

        Returns:
            SolidPython union of all cutouts
        """
        if not self.cutout_objects:
            self.generate_all_cutouts()

        if not self.cutout_objects:
            # No cutouts needed (all 1's pattern - should not happen with Gray code)
            return None

        return union()(*self.cutout_objects)

    def validate_track_spacing(self) -> Tuple[bool, List[str]]:
        """
        Validate that tracks fit within available space.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check total space required
        total_track_space = (
            self.params.num_tracks * self.params.track_width_mm
            + (self.params.num_tracks - 1) * self.params.track_spacing_mm
        )

        available_space = self.params.usable_radius_mm

        if total_track_space > available_space:
            errors.append(
                f"Tracks require {total_track_space:.1f}mm but only "
                f"{available_space:.1f}mm available"
            )

        # Check each track individually
        for track_idx in range(self.params.num_tracks):
            track_inner_radius = (
                self.params.radius_inner + track_idx * self.params.track_pitch_mm
            )
            track_outer_radius = track_inner_radius + self.params.track_width_mm

            if track_outer_radius > self.params.radius_outer:
                errors.append(f"Track {track_idx} extends beyond disk edge")

        return len(errors) == 0, errors

    def calculate_feature_sizes(self) -> Dict[str, Any]:
        """
        Calculate physical feature sizes for all tracks.

        Returns:
            Dictionary with feature size analysis
        """
        feature_analysis = {
            "tracks": [],
            "min_feature_size_mm": float("inf"),
            "max_feature_size_mm": 0,
            "printability_ok": True,
        }

        if not self.track_patterns:
            self.generate_all_tracks()

        for track_idx, pattern in enumerate(self.track_patterns):
            track_radius = (
                self.params.radius_inner
                + track_idx * self.params.track_pitch_mm
                + self.params.track_width_mm / 2
            )

            # Analyze run lengths
            runs = self._analyze_pattern_runs(pattern)

            track_info = {
                "track_index": track_idx,
                "radius_mm": track_radius,
                "runs": [],
                "min_feature_mm": float("inf"),
                "max_feature_mm": 0,
            }

            for run in runs:
                run_angle_deg = (
                    run["length"]
                    * self.params.arc_angle_deg
                    / self.params.num_positions
                )
                run_size_mm = (run_angle_deg * math.pi * track_radius) / 180

                run_info = {
                    "value": run["value"],
                    "length_positions": run["length"],
                    "angle_deg": run_angle_deg,
                    "size_mm": run_size_mm,
                }
                track_info["runs"].append(run_info)

                track_info["min_feature_mm"] = min(
                    track_info["min_feature_mm"], run_size_mm
                )
                track_info["max_feature_mm"] = max(
                    track_info["max_feature_mm"], run_size_mm
                )

                feature_analysis["min_feature_size_mm"] = min(
                    feature_analysis["min_feature_size_mm"], run_size_mm
                )
                feature_analysis["max_feature_size_mm"] = max(
                    feature_analysis["max_feature_size_mm"], run_size_mm
                )

            feature_analysis["tracks"].append(track_info)

        # Check printability
        min_printable = 0.5  # mm
        if feature_analysis["min_feature_size_mm"] < min_printable:
            feature_analysis["printability_ok"] = False

        return feature_analysis

    def _analyze_pattern_runs(self, pattern: List[int]) -> List[Dict[str, Any]]:
        """
        Analyze consecutive runs in a binary pattern.

        Args:
            pattern: List of 0/1 values

        Returns:
            List of run dictionaries with value and length
        """
        if not pattern:
            return []

        runs = []
        current_value = pattern[0]
        current_length = 1

        for i in range(1, len(pattern)):
            if pattern[i] == current_value:
                current_length += 1
            else:
                runs.append(
                    {
                        "value": current_value,
                        "length": current_length,
                        "start_index": i - current_length,
                    }
                )
                current_value = pattern[i]
                current_length = 1

        # Add final run
        runs.append(
            {
                "value": current_value,
                "length": current_length,
                "start_index": len(pattern) - current_length,
            }
        )

        return runs

    def export_pattern_data(self) -> Dict[str, Any]:
        """
        Export track pattern data for analysis and documentation.

        Returns:
            Dictionary with complete pattern information
        """
        if not self.track_patterns:
            self.generate_all_tracks()

        export_data = {
            "parameters": {
                "num_positions": self.params.num_positions,
                "num_tracks": self.params.num_tracks,
                "arc_angle_deg": self.params.arc_angle_deg,
            },
            "patterns": {},
            "gray_codes": [],
            "feature_analysis": self.calculate_feature_sizes(),
        }

        # Export Gray code sequence
        for pos in range(self.params.num_positions):
            bits = gray_code_bits(pos, self.params.num_tracks)
            gray_value = sum(
                bit * (2 ** (self.params.num_tracks - 1 - i))
                for i, bit in enumerate(bits)
            )
            export_data["gray_codes"].append(
                {"position": pos, "gray_value": gray_value, "bits": bits}
            )

        # Export track patterns
        for track_idx, pattern in enumerate(self.track_patterns):
            export_data["patterns"][f"track_{track_idx}"] = {
                "pattern": pattern,
                "runs": self._analyze_pattern_runs(pattern),
            }

        return export_data
