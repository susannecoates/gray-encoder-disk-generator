"""
Test suite for Gray code converter functions.
"""

import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gray_code.converter import (
    binary_to_gray,
    gray_to_binary,
    gray_code_bits,
    generate_gray_sequence,
    validate_gray_sequence,
    extract_track_pattern,
    analyze_track_transitions,
    calculate_encoding_efficiency,
    suggest_optimal_encoding,
)


class TestGrayCodeConverter(unittest.TestCase):
    """Test Gray code conversion functions."""

    def test_binary_to_gray_conversion(self):
        """Test binary to Gray code conversion."""
        # Known conversions
        test_cases = [
            (0, 0),  # 000 -> 000
            (1, 1),  # 001 -> 001
            (2, 3),  # 010 -> 011
            (3, 2),  # 011 -> 010
            (4, 6),  # 100 -> 110
            (5, 7),  # 101 -> 111
            (6, 5),  # 110 -> 101
            (7, 4),  # 111 -> 100
        ]

        for binary, expected_gray in test_cases:
            with self.subTest(binary=binary):
                result = binary_to_gray(binary)
                self.assertEqual(result, expected_gray)

    def test_gray_to_binary_conversion(self):
        """Test Gray code to binary conversion."""
        # Test round-trip conversion
        for i in range(16):
            with self.subTest(binary=i):
                gray = binary_to_gray(i)
                converted_back = gray_to_binary(gray)
                self.assertEqual(converted_back, i)

    def test_gray_code_bits_extraction(self):
        """Test bit extraction from Gray codes."""
        # Test 3-bit Gray code for position 5 (binary 101 -> Gray 111 = 0b111)
        # Now returns [LSB, ..., MSB] = [1, 1, 1]
        bits = gray_code_bits(5, 3)
        self.assertEqual(bits, [1, 1, 1])  # LSB=1, mid=1, MSB=1

        # Test 4-bit Gray code for position 10 (binary 1010 -> Gray 1111 = 0b1111)
        # Returns [LSB, ..., MSB] = [1, 1, 1, 1]
        bits = gray_code_bits(10, 4)
        self.assertEqual(bits, [1, 1, 1, 1])

        # Test edge case: position 0
        bits = gray_code_bits(0, 3)
        self.assertEqual(bits, [0, 0, 0])
        
        # Test position 3 (binary 011 -> Gray 010 = 0b010)
        # Returns [LSB, ..., MSB] = [0, 1, 0]
        bits = gray_code_bits(3, 3)
        self.assertEqual(bits, [0, 1, 0])

    def test_generate_gray_sequence(self):
        """Test Gray sequence generation."""
        # Generate 4-position sequence
        sequence = generate_gray_sequence(4)
        expected = [0, 1, 3, 2]  # Gray codes for 0,1,2,3
        self.assertEqual(sequence, expected)

        # Generate 8-position sequence
        sequence = generate_gray_sequence(8)
        expected = [0, 1, 3, 2, 6, 7, 5, 4]
        self.assertEqual(sequence, expected)

    def test_validate_gray_sequence(self):
        """Test Gray sequence validation."""
        # Valid sequence
        valid_sequence = [0, 1, 3, 2]
        is_valid, errors = validate_gray_sequence(valid_sequence)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Invalid sequence (2 bits differ)
        invalid_sequence = [0, 3, 1, 2]  # 0->3 differs in 2 bits
        is_valid, errors = validate_gray_sequence(invalid_sequence)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

        # Empty sequence
        is_valid, errors = validate_gray_sequence([])
        self.assertFalse(is_valid)

    def test_extract_track_pattern(self):
        """Test track pattern extraction."""
        # For 4 positions, 2 bits: Gray sequence = [0, 1, 3, 2]
        # Position 0 (Gray 0 = 0b00): bits [LSB=0, MSB=0]
        # Position 1 (Gray 1 = 0b01): bits [LSB=1, MSB=0]
        # Position 2 (Gray 3 = 0b11): bits [LSB=1, MSB=1]
        # Position 3 (Gray 2 = 0b10): bits [LSB=0, MSB=1]

        # Track 0 (LSB, outermost): [0,1,1,0] - most frequent changes
        pattern = extract_track_pattern(0, 4, 2)
        self.assertEqual(pattern, [0, 1, 1, 0])

        # Track 1 (MSB, innermost): [0,0,1,1] - least frequent changes
        pattern = extract_track_pattern(1, 4, 2)
        self.assertEqual(pattern, [0, 0, 1, 1])

    def test_analyze_track_transitions(self):
        """Test track transition analysis."""
        # Pattern with alternating bits
        pattern = [0, 1, 0, 1]
        analysis = analyze_track_transitions(pattern)

        self.assertEqual(analysis["total_positions"], 4)
        self.assertEqual(analysis["transitions"], 3)
        self.assertEqual(analysis["zero_count"], 2)
        self.assertEqual(analysis["one_count"], 2)

        # Pattern with runs
        pattern = [0, 0, 1, 1, 1, 0]
        analysis = analyze_track_transitions(pattern)

        self.assertEqual(analysis["transitions"], 2)  # 0→1, 1→0
        self.assertEqual(analysis["zero_runs"], [2, 1])
        self.assertEqual(analysis["one_runs"], [3])

    def test_calculate_encoding_efficiency(self):
        """Test encoding efficiency calculation."""
        # 32 positions with 5 bits (perfect efficiency)
        efficiency = calculate_encoding_efficiency(32, 5)
        self.assertEqual(efficiency["efficiency"], 1.0)
        self.assertEqual(efficiency["unused_codes"], 0)

        # 30 positions with 5 bits (some waste)
        efficiency = calculate_encoding_efficiency(30, 5)
        self.assertEqual(efficiency["unused_codes"], 2)
        self.assertLess(efficiency["efficiency"], 1.0)

    def test_suggest_optimal_encoding(self):
        """Test optimal encoding suggestions."""
        # 32 positions (power of 2)
        suggestion = suggest_optimal_encoding(32)
        self.assertEqual(suggestion["minimum_bits"], 5)
        self.assertEqual(suggestion["optimal_positions"], 32)
        self.assertEqual(suggestion["efficiency"], 1.0)

        # 30 positions (not power of 2)
        suggestion = suggest_optimal_encoding(30)
        self.assertEqual(suggestion["minimum_bits"], 5)
        self.assertLess(suggestion["efficiency"], 1.0)


if __name__ == "__main__":
    unittest.main()
