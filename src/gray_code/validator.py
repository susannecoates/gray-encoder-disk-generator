"""
Validation utilities for Gray code patterns and encoder designs.

This module provides functions to validate Gray code implementations
and detect potential issues in encoder patterns.
"""

from typing import List, Tuple, Dict, Any
from .converter import (
    gray_code_bits,
    extract_track_pattern,
    analyze_track_transitions,
    validate_gray_sequence,
    generate_gray_sequence,
)


class GrayCodeValidator:
    """Comprehensive validator for Gray code encoder patterns."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def validate_encoder_pattern(
        self, num_positions: int, num_tracks: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate complete encoder Gray code pattern.

        Args:
            num_positions: Number of positions to encode
            num_tracks: Number of tracks (bits) available

        Returns:
            Tuple of (is_valid, validation_report)
        """
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()

        # Generate and validate sequence
        sequence = generate_gray_sequence(num_positions)
        seq_valid, seq_errors = validate_gray_sequence(sequence)

        if not seq_valid:
            self.errors.extend(seq_errors)

        # Validate track patterns
        track_analyses = {}
        for track_idx in range(num_tracks):
            pattern = extract_track_pattern(track_idx, num_positions, num_tracks)
            analysis = analyze_track_transitions(pattern)
            track_analyses[f"track_{track_idx}"] = analysis

            self._validate_track_pattern(track_idx, pattern, analysis)

        # Check overall encoding efficiency
        self._validate_encoding_efficiency(num_positions, num_tracks)

        # Generate report
        report = {
            "is_valid": len(self.errors) == 0,
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy(),
            "info": self.info.copy(),
            "gray_sequence": sequence,
            "track_analyses": track_analyses,
            "summary": self._generate_summary(
                num_positions, num_tracks, track_analyses
            ),
        }

        return len(self.errors) == 0, report

    def _validate_track_pattern(
        self, track_idx: int, pattern: List[int], analysis: dict
    ):
        """Validate individual track pattern."""
        # Check for extremely short runs (may be unprintable)
        if analysis.get("min_zero_run", 0) == 1:
            self.warnings.append(
                f"Track {track_idx}: Single-position zero runs may be hard to print"
            )

        if analysis.get("min_one_run", 0) == 1:
            self.warnings.append(
                f"Track {track_idx}: Single-position one runs may be hard to print"
            )

        # Check for very long runs (may cause sensor alignment issues)
        max_run_threshold = max(8, len(pattern) // 4)
        if analysis.get("max_zero_run", 0) > max_run_threshold:
            self.warnings.append(
                f"Track {track_idx}: Very long zero run "
                f"({analysis['max_zero_run']} positions)"
            )

        if analysis.get("max_one_run", 0) > max_run_threshold:
            self.warnings.append(
                f"Track {track_idx}: Very long one run "
                f"({analysis['max_one_run']} positions)"
            )

        # Check balance
        zero_percent = (
            analysis.get("zero_count", 0) / analysis.get("total_positions", 1)
        ) * 100
        if zero_percent < 25 or zero_percent > 75:
            self.warnings.append(
                f"Track {track_idx}: Unbalanced pattern ({zero_percent:.1f}% zeros)"
            )

        # Track-specific recommendations
        if track_idx == 0:  # Outermost track (LSB)
            self.info.append(
                f"Track {track_idx} (LSB, outermost): "
                f"{analysis['transitions']} transitions, "
                f"fastest changing track"
            )
        elif track_idx == len(pattern) - 1:  # Innermost track (MSB)
            self.info.append(
                f"Track {track_idx} (MSB, innermost): "
                f"{analysis['transitions']} transitions"
            )

    def _validate_encoding_efficiency(self, num_positions: int, num_tracks: int):
        """Validate encoding efficiency."""
        import math

        max_positions = 2**num_tracks
        efficiency = num_positions / max_positions

        if efficiency < 0.5:
            self.warnings.append(
                f"Low encoding efficiency: {efficiency:.1%} "
                f"({num_positions}/{max_positions} codes used)"
            )
        elif efficiency < 0.75:
            self.warnings.append(f"Moderate encoding efficiency: {efficiency:.1%}")
        else:
            self.info.append(f"Good encoding efficiency: {efficiency:.1%}")

        # Check if we could use fewer tracks
        min_tracks = math.ceil(math.log2(num_positions))
        if num_tracks > min_tracks:
            unused_tracks = num_tracks - min_tracks
            self.info.append(
                f"Could reduce from {num_tracks} to {min_tracks} tracks "
                f"(saving {unused_tracks} track{'s' if unused_tracks > 1 else ''})"
            )

    def _generate_summary(
        self, num_positions: int, num_tracks: int, track_analyses: dict
    ) -> dict:
        """Generate summary statistics."""
        total_transitions = sum(
            analysis.get("transitions", 0) for analysis in track_analyses.values()
        )

        avg_transitions = total_transitions / num_tracks if num_tracks > 0 else 0

        # Find most and least active tracks
        track_transitions = [
            (idx, analysis.get("transitions", 0))
            for idx, analysis in enumerate(track_analyses.values())
        ]
        track_transitions.sort(key=lambda x: x[1])

        return {
            "num_positions": num_positions,
            "num_tracks": num_tracks,
            "total_transitions": total_transitions,
            "avg_transitions_per_track": avg_transitions,
            "most_active_track": track_transitions[-1] if track_transitions else None,
            "least_active_track": track_transitions[0] if track_transitions else None,
            "encoding_efficiency": num_positions / (2**num_tracks)
            if num_tracks > 0
            else 0,
        }


def validate_physical_constraints(
    patterns: List[List[int]], params
) -> Tuple[bool, List[str]]:
    """
    Validate Gray code patterns against physical manufacturing constraints.

    Args:
        patterns: List of track patterns (each pattern is list of 0/1 values)
        params: EncoderParameters object

    Returns:
        Tuple of (is_valid, issues)
    """
    import math

    issues = []

    for track_idx, pattern in enumerate(patterns):
        # Calculate physical dimensions of features
        track_radius = (
            params.radius_inner
            + track_idx * (params.track_width_mm + params.track_spacing_mm)
            + params.track_width_mm / 2
        )

        # Analyze runs for physical size
        current_run = 1
        current_value = pattern[0] if pattern else 0
        min_feature_size = float("inf")

        for i in range(1, len(pattern)):
            if pattern[i] == current_value:
                current_run += 1
            else:
                # Calculate physical size of this run
                run_angle_deg = (current_run * params.arc_angle_deg) / len(pattern)
                run_size_mm = (run_angle_deg * math.pi * track_radius) / 180

                min_feature_size = min(min_feature_size, run_size_mm)

                if run_size_mm < 0.5:  # Minimum printable feature
                    issues.append(
                        f"Track {track_idx}: Feature size {run_size_mm:.2f}mm "
                        f"too small (minimum 0.5mm)"
                    )

                current_run = 1
                current_value = pattern[i]

        # Check final run
        if current_run > 0:
            run_angle_deg = (current_run * params.arc_angle_deg) / len(pattern)
            run_size_mm = (run_angle_deg * math.pi * track_radius) / 180
            min_feature_size = min(min_feature_size, run_size_mm)

    return len(issues) == 0, issues


def generate_test_patterns(
    num_positions: int, num_tracks: int
) -> Dict[str, List[List[int]]]:
    """
    Generate test patterns for validation and debugging.

    Args:
        num_positions: Number of positions
        num_tracks: Number of tracks

    Returns:
        Dictionary of test patterns
    """
    patterns = {}

    # Standard Gray code pattern
    gray_patterns = []
    for track_idx in range(num_tracks):
        pattern = extract_track_pattern(track_idx, num_positions, num_tracks)
        gray_patterns.append(pattern)
    patterns["gray_code"] = gray_patterns

    # Binary pattern (for comparison)
    binary_patterns = []
    for track_idx in range(num_tracks):
        pattern = []
        for pos in range(num_positions):
            bit = (pos >> (num_tracks - 1 - track_idx)) & 1
            pattern.append(bit)
        binary_patterns.append(pattern)
    patterns["binary"] = binary_patterns

    # Alternating pattern (for testing)
    alt_patterns = []
    for track_idx in range(num_tracks):
        pattern = [i % 2 for i in range(num_positions)]
        alt_patterns.append(pattern)
    patterns["alternating"] = alt_patterns

    return patterns
