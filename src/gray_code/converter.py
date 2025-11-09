"""
Gray code conversion and validation utilities.

This module implements Gray code mathematics for absolute position encoding
in optical encoder applications.
"""

from typing import List, Tuple
import math


def binary_to_gray(n: int) -> int:
    """
    Convert binary number to Gray code.

    Args:
        n: Binary number to convert

    Returns:
        Gray code equivalent
    """
    return n ^ (n >> 1)


def gray_to_binary(gray: int) -> int:
    """
    Convert Gray code to binary number.

    Args:
        gray: Gray code to convert

    Returns:
        Binary equivalent
    """
    binary = gray
    while gray:
        gray >>= 1
        binary ^= gray
    return binary


def gray_code_bits(position: int, num_bits: int) -> List[int]:
    """
    Extract individual bits from Gray code representation of position.

    Args:
        position: Position to encode (0 to 2^num_bits - 1)
        num_bits: Number of bits in encoding

    Returns:
        List of bits [LSB, ..., MSB] where each bit is 0 or 1
        LSB (index 0) is placed on outermost track (most frequent changes)
        MSB (index n-1) is placed on innermost track (least frequent changes)
    """
    gray_value = binary_to_gray(position)
    return [(gray_value >> i) & 1 for i in range(num_bits)]


def generate_gray_sequence(num_positions: int) -> List[int]:
    """
    Generate complete Gray code sequence for given number of positions.

    Args:
        num_positions: Number of positions to encode

    Returns:
        List of Gray codes for positions 0 to num_positions-1
    """
    return [binary_to_gray(i) for i in range(num_positions)]


def validate_gray_sequence(sequence: List[int]) -> Tuple[bool, List[str]]:
    """
    Validate that a Gray code sequence has proper single-bit transitions.

    Args:
        sequence: List of Gray codes to validate

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if not sequence:
        errors.append("Empty sequence")
        return False, errors

    # Check each transition
    for i in range(len(sequence) - 1):
        current = sequence[i]
        next_code = sequence[i + 1]

        # XOR to find differing bits
        diff = current ^ next_code

        # Count number of differing bits
        bit_count = bin(diff).count("1")

        if bit_count != 1:
            errors.append(
                f"Position {i} to {i+1}: {bit_count} bits differ "
                f"(should be 1) - {current:b} -> {next_code:b}"
            )

    # Check for duplicates
    if len(set(sequence)) != len(sequence):
        errors.append("Duplicate Gray codes found in sequence")

    return len(errors) == 0, errors


def extract_track_pattern(
    track_index: int, num_positions: int, num_bits: int
) -> List[int]:
    """
    Extract the binary pattern for a specific track across all positions.

    Args:
        track_index: Index of track (0 = outermost/LSB, num_bits-1 = innermost/MSB)
        num_positions: Total number of positions
        num_bits: Number of bits in Gray code

    Returns:
        List of binary values (0 or 1) for this track at each position
        Track 0 (outermost) gets LSB (most frequent changes)
        Track n-1 (innermost) gets MSB (least frequent changes)
    """
    pattern = []
    for position in range(num_positions):
        bits = gray_code_bits(position, num_bits)
        pattern.append(bits[track_index])
    return pattern


def analyze_track_transitions(track_pattern: List[int]) -> dict:
    """
    Analyze transition characteristics of a track pattern.

    Args:
        track_pattern: List of binary values for a track

    Returns:
        Dictionary with transition analysis
    """
    if not track_pattern:
        return {"error": "Empty pattern"}

    transitions = 0
    zero_runs = []
    one_runs = []
    current_run = 1
    current_value = track_pattern[0]

    # Count transitions and run lengths
    for i in range(1, len(track_pattern)):
        if track_pattern[i] == current_value:
            current_run += 1
        else:
            # Transition occurred
            transitions += 1
            if current_value == 0:
                zero_runs.append(current_run)
            else:
                one_runs.append(current_run)
            current_run = 1
            current_value = track_pattern[i]

    # Add final run
    if current_value == 0:
        zero_runs.append(current_run)
    else:
        one_runs.append(current_run)

    # Calculate statistics
    total_zeros = sum(zero_runs) if zero_runs else 0
    total_ones = sum(one_runs) if one_runs else 0

    return {
        "total_positions": len(track_pattern),
        "transitions": transitions,
        "zero_count": total_zeros,
        "one_count": total_ones,
        "zero_runs": zero_runs,
        "one_runs": one_runs,
        "min_zero_run": min(zero_runs) if zero_runs else 0,
        "max_zero_run": max(zero_runs) if zero_runs else 0,
        "min_one_run": min(one_runs) if one_runs else 0,
        "max_one_run": max(one_runs) if one_runs else 0,
        "avg_zero_run": sum(zero_runs) / len(zero_runs) if zero_runs else 0,
        "avg_one_run": sum(one_runs) / len(one_runs) if one_runs else 0,
    }


def calculate_encoding_efficiency(num_positions: int, num_bits: int) -> dict:
    """
    Calculate efficiency metrics for Gray code encoding.

    Args:
        num_positions: Number of positions to encode
        num_bits: Number of bits used

    Returns:
        Dictionary with efficiency metrics
    """
    max_positions = 2**num_bits
    unused_codes = max_positions - num_positions
    efficiency = num_positions / max_positions

    return {
        "num_positions": num_positions,
        "num_bits": num_bits,
        "max_positions": max_positions,
        "unused_codes": unused_codes,
        "efficiency": efficiency,
        "efficiency_percent": efficiency * 100,
        "wasted_tracks": math.ceil(math.log2(unused_codes)) if unused_codes > 0 else 0,
    }


def suggest_optimal_encoding(target_positions: int) -> dict:
    """
    Suggest optimal bit count for a target number of positions.

    Args:
        target_positions: Desired number of positions

    Returns:
        Dictionary with encoding recommendations
    """
    min_bits = math.ceil(math.log2(target_positions))
    optimal_positions = 2**min_bits

    # Also consider next power of 2 if efficiency is poor
    next_bits = min_bits + 1
    next_positions = 2**next_bits

    current_efficiency = target_positions / optimal_positions

    recommendations = {
        "target_positions": target_positions,
        "minimum_bits": min_bits,
        "optimal_positions": optimal_positions,
        "efficiency": current_efficiency,
        "recommendation": "optimal"
        if current_efficiency >= 0.75
        else "consider_rounding",
    }

    if current_efficiency < 0.75:
        recommendations.update(
            {
                "alternative_positions": optimal_positions,
                "alternative_efficiency": 1.0,
                "next_power_positions": next_positions,
                "next_power_bits": next_bits,
                "suggestion": f"Consider using {optimal_positions} positions for 100% efficiency",
            }
        )

    return recommendations
