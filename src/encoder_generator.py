#!/usr/bin/env python3
"""
Rudder Encoder Disk Generator

Main script for generating 3D printable optical encoder disks for sailboat
rudder position sensing using Gray code absolute positioning.

Usage:
    python encoder_generator.py [options]

Options:
    --config CONFIG_NAME    Use predefined configuration (default, high_res, compact)
    --output OUTPUT_FILE    Output .scad filename (default: gray_encoder_disk.scad)
    --validate              Validate design without generating output
    --info                  Show detailed design information
    --export-data           Export pattern data to JSON
    --no-bumpers           Generate disk without limit switch bumpers

Examples:
    python encoder_generator.py --config high_res --output high_res_encoder.scad
    python encoder_generator.py --validate --info
    python encoder_generator.py --no-bumpers --output encoder_no_bumpers.scad
"""

import argparse
import json
import sys
import os
from pathlib import Path

from solid import scad_render_to_file
from solid.utils import *

# Add src to path for imports
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from utils import (
    EncoderParameters,
    ParameterValidator,
    create_default_parameters,
    create_high_resolution_parameters,
    create_compact_parameters,
    PrintabilityAnalyzer,
)
from gray_code import GrayCodeValidator
from geometry import EncoderAssembler


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate 3D printable optical encoder disks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1] if "Usage:" in __doc__ else "",
    )

    parser.add_argument(
        "--config",
        choices=["default", "high_res", "compact", "custom"],
        default="default",
        help="Predefined parameter configuration to use",
    )

    parser.add_argument(
        "--params",
        help="JSON file containing custom parameters (required when --config=custom)",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="output/gray_encoder_disk.scad",
        help="Output .scad filename",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate design parameters without generating output",
    )

    parser.add_argument(
        "--info", action="store_true", help="Show detailed design information"
    )

    parser.add_argument(
        "--export-data", help="Export pattern data to specified JSON file"
    )

    parser.add_argument(
        "--no-bumpers",
        action="store_true",
        help="Generate disk without limit switch bumpers",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    return parser.parse_args()


def load_configuration(config_name: str, params_file: str = None) -> EncoderParameters:
    """Load predefined parameter configuration or custom parameters from file."""
    if config_name == "custom":
        if not params_file:
            raise ValueError("--params file required when using --config=custom")

        if not os.path.exists(params_file):
            raise FileNotFoundError(f"Parameters file not found: {params_file}")

        try:
            with open(params_file, "r") as f:
                params_dict = json.load(f)
            return EncoderParameters(**params_dict)
        except Exception as e:
            raise ValueError(f"Failed to load parameters from {params_file}: {e}")

    config_map = {
        "default": create_default_parameters,
        "high_res": create_high_resolution_parameters,
        "compact": create_compact_parameters,
    }

    if config_name not in config_map:
        raise ValueError(f"Unknown configuration: {config_name}")

    return config_map[config_name]()


def validate_design(params: EncoderParameters, verbose: bool = False) -> bool:
    """
    Perform comprehensive design validation.

    Args:
        params: EncoderParameters to validate
        verbose: Whether to show detailed output

    Returns:
        True if design is valid
    """
    print("🔍 Validating encoder design...")

    # Parameter validation
    param_validator = ParameterValidator(params)
    param_valid, param_errors, param_warnings = param_validator.validate_all()

    # Gray code validation
    gray_validator = GrayCodeValidator()
    gray_valid, gray_report = gray_validator.validate_encoder_pattern(
        params.num_positions, params.num_tracks
    )

    # Printability validation
    print_analyzer = PrintabilityAnalyzer()
    (
        print_valid,
        print_issues,
        print_recommendations,
    ) = print_analyzer.analyze_encoder_design(params)

    # Report results
    overall_valid = param_valid and gray_valid and print_valid

    if param_errors:
        print(" Parameter Errors:")
        for error in param_errors:
            print(f"   • {error}")

    if param_warnings:
        print("  Parameter Warnings:")
        for warning in param_warnings:
            print(f"   • {warning}")

    if not gray_valid:
        print(" Gray Code Errors:")
        for error in gray_report["errors"]:
            print(f"   • {error}")

    if gray_report["warnings"]:
        print("  Gray Code Warnings:")
        for warning in gray_report["warnings"]:
            print(f"   • {warning}")

    if print_issues:
        print(" Printability Issues:")
        for issue in print_issues:
            print(f"   • {issue}")

    if verbose and print_recommendations:
        print("💡 Printing Recommendations:")
        for rec in print_recommendations:
            print(f"   • {rec}")

    if overall_valid:
        print(" Design validation passed!")
    else:
        print(" Design validation failed!")

    return overall_valid


def show_design_info(params: EncoderParameters):
    """Show detailed design information."""
    print("\n Encoder Design Information")
    print("=" * 50)

    print(f"Physical Dimensions:")
    print(f"  • Outer diameter: {params.outer_diameter_mm}mm")
    print(f"  • Inner diameter: {params.inner_diameter_mm}mm")
    print(f"  • Thickness: {params.disk_thickness_mm}mm")
    print(f"  • Arc angle: {params.arc_angle_deg}°")

    print(f"\nEncoding Specifications:")
    print(f"  • Positions: {params.num_positions}")
    print(f"  • Tracks: {params.num_tracks}")
    print(f"  • Angular resolution: {params.angular_resolution_deg:.3f}°")
    print(f"  • Required bits: {params.required_bits}")

    efficiency = params.num_positions / (2**params.num_tracks)
    print(f"  • Encoding efficiency: {efficiency:.1%}")

    print(f"\nTrack Layout:")
    print(f"  • Track width: {params.track_width_mm}mm")
    print(f"  • Track spacing: {params.track_spacing_mm}mm")
    print(f"  • Track pitch: {params.track_pitch_mm}mm")
    print(f"  • Usable radius: {params.usable_radius_mm}mm")

    print(f"\nLimit Switch Bumpers:")
    print(f"  • Extension: {params.bump_extension_mm}mm")
    print(f"  • Width: {params.bump_width_deg}°")

    # Create assembler to get detailed info
    assembler = EncoderAssembler(params)
    assembler.track_generator.generate_all_tracks()
    assembly_info = assembler.get_assembly_info()

    print(f"\nCalculated Properties:")
    print(f"  • Disk area: {assembly_info['geometry']['total_area_mm2']:.1f}mm²")
    print(
        f"  • Outer arc length: "
        f"{assembly_info['geometry']['arc_length_outer_mm']:.1f}mm"
    )

    feature_analysis = assembly_info["manufacturing"]
    if feature_analysis["printability_ok"]:
        print(f"  • Minimum feature: {feature_analysis['min_feature_size_mm']:.2f}mm ")
    else:
        print(f"  • Minimum feature: {feature_analysis['min_feature_size_mm']:.2f}mm ")


def generate_encoder(
    params: EncoderParameters,
    output_file: str,
    include_bumpers: bool = True,
    verbose: bool = False,
) -> bool:
    """
    Generate the encoder disk 3D model.

    Args:
        params: EncoderParameters to use
        output_file: Output .scad filename
        include_bumpers: Whether to include limit switch bumpers
        verbose: Whether to show progress

    Returns:
        True if generation successful
    """
    try:
        if verbose:
            print(f" Generating encoder disk...")

        # Create assembler and generate disk
        assembler = EncoderAssembler(params)
        encoder_disk = assembler.assemble_complete_disk(include_bumpers=include_bumpers)

        # Validate assembly
        assembly_valid, assembly_errors = assembler.validate_assembly()
        if not assembly_valid:
            print(" Assembly validation failed:")
            for error in assembly_errors:
                print(f"   • {error}")
            return False

        # Generate OpenSCAD file
        if verbose:
            print(f"💾 Writing to {output_file}...")

        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Add header comment
        header_comment = f"""//
// Rudder Encoder Disk
// Generated by encoder_generator.py
//
// Parameters:
//   Positions: {params.num_positions}
//   Tracks: {params.num_tracks}
//   Arc angle: {params.arc_angle_deg}°
//   Outer diameter: {params.outer_diameter_mm}mm
//   Inner diameter: {params.inner_diameter_mm}mm
//   Thickness: {params.disk_thickness_mm}mm
//   Bumpers: {'Yes' if include_bumpers else 'No'}
//
// Print Settings Recommendations:
//   Layer height: 0.2mm
//   Perimeters: 3
//   Infill: 20%
//   Print speed: 50mm/s (perimeters), 100mm/s (infill)
//   Material: PETG or ASA for UV resistance
//
"""

        scad_render_to_file(encoder_disk, output_file, file_header=header_comment)

        print(f" Encoder disk generated successfully: {output_file}")

        if verbose:
            file_size = os.path.getsize(output_file)
            print(f"   File size: {file_size:,} bytes")

        return True

    except Exception as e:
        print(f" Error generating encoder: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        return False


def export_pattern_data(params: EncoderParameters, output_file: str) -> bool:
    """
    Export pattern data to JSON file.

    Args:
        params: EncoderParameters to use
        output_file: Output JSON filename

    Returns:
        True if export successful
    """
    try:
        # Ensure output directory exists for pattern data
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        assembler = EncoderAssembler(params)
        pattern_data = assembler.track_generator.export_pattern_data()

        # Add parameter info
        export_data = {
            "metadata": {
                "generator": "encoder_generator.py",
                "version": "1.0.0",
                "description": "Gray code optical encoder disk pattern data",
            },
            "parameters": {
                "outer_diameter_mm": params.outer_diameter_mm,
                "inner_diameter_mm": params.inner_diameter_mm,
                "disk_thickness_mm": params.disk_thickness_mm,
                "arc_angle_deg": params.arc_angle_deg,
                "num_positions": params.num_positions,
                "num_tracks": params.num_tracks,
                "track_width_mm": params.track_width_mm,
                "track_spacing_mm": params.track_spacing_mm,
            },
            "pattern_data": pattern_data,
        }

        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f" Pattern data exported: {output_file}")
        return True

    except Exception as e:
        print(f" Error exporting pattern data: {e}")
        return False


def main():
    """Main entry point."""
    args = parse_arguments()

    print("🚢 Rudder Encoder Disk Generator")
    print("=" * 40)

    try:
        # Load configuration
        params = load_configuration(args.config, args.params)
        print(f"📋 Using configuration: {args.config}")

        # Show design info if requested
        if args.info:
            show_design_info(params)

        # Validate design
        if not validate_design(params, args.verbose):
            if not args.validate:  # If just validating, continue anyway
                print("  Validation failed, but continuing generation...")
            else:
                return 1

        # Export pattern data if requested
        if args.export_data:
            if not export_pattern_data(params, args.export_data):
                return 1

        # Generate encoder (unless just validating)
        if not args.validate:
            if not generate_encoder(
                params, args.output, not args.no_bumpers, args.verbose
            ):
                return 1

        print("\n🎉 Operation completed successfully!")
        return 0

    except KeyboardInterrupt:
        print("\n  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
