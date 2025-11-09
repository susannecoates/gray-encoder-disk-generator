"""
Test suite for geometry functions.
"""

import unittest
import math
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from geometry.arc_utils import (
    create_arc_points,
    create_sector_points,
    calculate_arc_length,
    calculate_sector_area,
    calculate_chord_length,
    validate_arc_parameters,
    optimize_segment_count,
)


class TestArcUtils(unittest.TestCase):
    """Test arc utility functions."""

    def test_create_arc_points(self):
        """Test arc point generation."""
        # Quarter circle
        points = create_arc_points(10, 0, 90, 4)

        # Should have 5 points (including endpoints)
        self.assertEqual(len(points), 5)

        # First point should be at (10, 0)
        self.assertAlmostEqual(points[0][0], 10, places=5)
        self.assertAlmostEqual(points[0][1], 0, places=5)

        # Last point should be at (0, 10)
        self.assertAlmostEqual(points[-1][0], 0, places=5)
        self.assertAlmostEqual(points[-1][1], 10, places=5)

    def test_create_sector_points(self):
        """Test sector point generation."""
        # Sector from 0 to 90 degrees
        points = create_sector_points(5, 10, 0, 90, 4)

        # Should form closed polygon: outer arc + inner arc
        self.assertGreater(len(points), 8)  # At least 4 outer + 4 inner

        # First point should be on outer radius
        distance_from_origin = math.sqrt(points[0][0] ** 2 + points[0][1] ** 2)
        self.assertAlmostEqual(distance_from_origin, 10, places=5)

    def test_calculate_arc_length(self):
        """Test arc length calculation."""
        # Half circle with radius 10
        arc_length = calculate_arc_length(10, 180)
        expected = math.pi * 10
        self.assertAlmostEqual(arc_length, expected, places=5)

        # Quarter circle with radius 5
        arc_length = calculate_arc_length(5, 90)
        expected = math.pi * 5 / 2
        self.assertAlmostEqual(arc_length, expected, places=5)

    def test_calculate_sector_area(self):
        """Test sector area calculation."""
        # Half annulus
        area = calculate_sector_area(5, 10, 180)
        expected = 0.5 * math.pi * (10**2 - 5**2)
        self.assertAlmostEqual(area, expected, places=5)

        # Full annulus
        area = calculate_sector_area(3, 7, 360)
        expected = math.pi * (7**2 - 3**2)
        self.assertAlmostEqual(area, expected, places=5)

    def test_calculate_chord_length(self):
        """Test chord length calculation."""
        # 90 degree chord on unit circle
        chord = calculate_chord_length(1, 90)
        expected = math.sqrt(2)
        self.assertAlmostEqual(chord, expected, places=5)

        # 60 degree chord on unit circle
        chord = calculate_chord_length(1, 60)
        expected = 1  # Equilateral triangle
        self.assertAlmostEqual(chord, expected, places=5)

    def test_validate_arc_parameters(self):
        """Test arc parameter validation."""
        # Valid parameters
        is_valid, errors = validate_arc_parameters(5, 10, 0, 90)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Invalid: outer <= inner
        is_valid, errors = validate_arc_parameters(10, 5, 0, 90)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

        # Invalid: negative inner radius
        is_valid, errors = validate_arc_parameters(-1, 10, 0, 90)
        self.assertFalse(is_valid)

        # Invalid: end <= start angle
        is_valid, errors = validate_arc_parameters(5, 10, 90, 45)
        self.assertFalse(is_valid)

    def test_optimize_segment_count(self):
        """Test segment count optimization."""
        # Large radius needs more segments for same chord error
        segments_large = optimize_segment_count(100, 90, 0.1)

        # Small radius needs fewer segments for same chord error
        segments_small = optimize_segment_count(1, 90, 0.1)

        self.assertGreater(segments_large, segments_small)

        # Very small error tolerance should require more segments
        segments_fine = optimize_segment_count(10, 90, 0.01)
        segments_coarse = optimize_segment_count(10, 90, 1.0)

        self.assertGreater(segments_fine, segments_coarse)


class TestParameterValidation(unittest.TestCase):
    """Test parameter validation."""

    def setUp(self):
        """Set up test parameters."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
        from utils.parameters import EncoderParameters, ParameterValidator

        self.EncoderParameters = EncoderParameters
        self.ParameterValidator = ParameterValidator

    def test_valid_default_parameters(self):
        """Test that default parameters are valid."""
        params = self.EncoderParameters()
        validator = self.ParameterValidator(params)

        is_valid, errors, warnings = validator.validate_all()

        # Default parameters should be valid
        self.assertTrue(is_valid, f"Default parameters failed validation: {errors}")

    def test_invalid_geometry(self):
        """Test detection of invalid geometry."""
        params = self.EncoderParameters()
        params.outer_diameter_mm = 20  # Smaller than inner
        params.inner_diameter_mm = 30

        validator = self.ParameterValidator(params)
        is_valid, errors, warnings = validator.validate_all()

        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_encoding_mismatch(self):
        """Test detection of encoding mismatches."""
        params = self.EncoderParameters()
        params.num_positions = 32  # Requires 5 bits
        params.num_tracks = 8  # But using 8 tracks

        validator = self.ParameterValidator(params)
        is_valid, errors, warnings = validator.validate_all()

        # Should have an error about mismatched track count
        self.assertFalse(is_valid)
        track_error = any("Track count" in error for error in errors)
        self.assertTrue(track_error)


if __name__ == "__main__":
    unittest.main()
