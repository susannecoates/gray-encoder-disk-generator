"""Gray code utilities for optical encoder generation."""

from .converter import (
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

from .validator import (
    GrayCodeValidator,
    validate_physical_constraints,
    generate_test_patterns,
)

__all__ = [
    "binary_to_gray",
    "gray_to_binary",
    "gray_code_bits",
    "generate_gray_sequence",
    "validate_gray_sequence",
    "extract_track_pattern",
    "analyze_track_transitions",
    "calculate_encoding_efficiency",
    "suggest_optimal_encoding",
    "GrayCodeValidator",
    "validate_physical_constraints",
    "generate_test_patterns",
]
