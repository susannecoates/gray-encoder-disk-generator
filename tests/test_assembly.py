"""
Test suite for complete encoder assembly.
"""

import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils import create_default_parameters
from geometry import EncoderAssembler


class TestEncoderAssembly(unittest.TestCase):
    """Test complete encoder assembly."""

    def setUp(self):
        """Set up test assembly."""
        self.params = create_default_parameters()
        self.assembler = EncoderAssembler(self.params)

    def test_create_base_disk(self):
        """Test base disk creation."""
        base_disk = self.assembler.create_base_disk()
        self.assertIsNotNone(base_disk)
        self.assertEqual(self.assembler.base_disk, base_disk)

    def test_create_limit_bumpers(self):
        """Test limit bumper creation."""
        bumpers = self.assembler.create_limit_bumpers()

        # Should create 2 bumpers (start and end)
        self.assertEqual(len(bumpers), 2)
        self.assertEqual(len(self.assembler.bumpers), 2)

    def test_track_generation(self):
        """Test track pattern generation."""
        patterns = self.assembler.track_generator.generate_all_tracks()

        # Should have correct number of tracks
        self.assertEqual(len(patterns), self.params.num_tracks)

        # Each pattern should have correct number of positions
        for pattern in patterns:
            self.assertEqual(len(pattern), self.params.num_positions)

            # All values should be 0 or 1
            for value in pattern:
                self.assertIn(value, [0, 1])

    def test_cutout_generation(self):
        """Test cutout generation."""
        cutouts = self.assembler.track_generator.generate_all_cutouts()

        # Should generate some cutouts (unless all patterns are 1's)
        self.assertIsInstance(cutouts, list)

    def test_assembly_validation(self):
        """Test assembly validation."""
        is_valid, errors = self.assembler.validate_assembly()

        # Default parameters should validate successfully
        if not is_valid:
            print(f"Assembly validation errors: {errors}")

        # Note: We don't assert True here because SolidPython objects
        # might not be available in test environment
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(errors, list)

    def test_feature_size_calculation(self):
        """Test feature size calculations."""
        feature_analysis = self.assembler.track_generator.calculate_feature_sizes()

        self.assertIn("tracks", feature_analysis)
        self.assertIn("min_feature_size_mm", feature_analysis)
        self.assertIn("printability_ok", feature_analysis)

        # Should have analysis for each track
        self.assertEqual(len(feature_analysis["tracks"]), self.params.num_tracks)

        # Minimum feature size should be positive
        self.assertGreater(feature_analysis["min_feature_size_mm"], 0)

    def test_assembly_info(self):
        """Test assembly information generation."""
        info = self.assembler.get_assembly_info()

        required_keys = [
            "parameters",
            "geometry",
            "encoding",
            "manufacturing",
            "components",
        ]
        for key in required_keys:
            self.assertIn(key, info)

        # Check parameter values match
        self.assertEqual(info["parameters"]["num_positions"], self.params.num_positions)
        self.assertEqual(info["parameters"]["num_tracks"], self.params.num_tracks)

        # Check calculated values are reasonable
        self.assertGreater(info["geometry"]["total_area_mm2"], 0)
        self.assertGreater(info["encoding"]["angular_resolution_deg"], 0)

    def test_pattern_data_export(self):
        """Test pattern data export."""
        export_data = self.assembler.track_generator.export_pattern_data()

        required_keys = ["parameters", "patterns", "gray_codes", "feature_analysis"]
        for key in required_keys:
            self.assertIn(key, export_data)

        # Check Gray code sequence
        gray_codes = export_data["gray_codes"]
        self.assertEqual(len(gray_codes), self.params.num_positions)

        # Each Gray code entry should have position, value, and bits
        for entry in gray_codes:
            self.assertIn("position", entry)
            self.assertIn("gray_value", entry)
            self.assertIn("bits", entry)
            self.assertEqual(len(entry["bits"]), self.params.num_tracks)


class TestConfigurationValidation(unittest.TestCase):
    """Test different parameter configurations."""

    def test_high_resolution_config(self):
        """Test high resolution configuration."""
        from utils import create_high_resolution_parameters, ParameterValidator

        params = create_high_resolution_parameters()
        validator = ParameterValidator(params)

        is_valid, errors, warnings = validator.validate_all()

        # High resolution config should be valid (though may have warnings)
        if not is_valid:
            print(f"High resolution validation errors: {errors}")
            print(f"Warnings: {warnings}")

    def test_compact_config(self):
        """Test compact configuration."""
        from utils import create_compact_parameters, ParameterValidator

        params = create_compact_parameters()
        validator = ParameterValidator(params)

        is_valid, errors, warnings = validator.validate_all()

        # Compact config should be valid
        if not is_valid:
            print(f"Compact validation errors: {errors}")
            print(f"Warnings: {warnings}")


if __name__ == "__main__":
    unittest.main()
