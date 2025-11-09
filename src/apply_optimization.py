"""
Apply optimized parameters to the default configuration.

This script reads optimized parameters from genetic algorithm results
and updates the default parameter configuration.
"""

import json
import sys
import os
from pathlib import Path


def update_default_parameters(optimization_results_file: str):
    """Update default parameters with optimization results."""

    # Read optimization results
    if not os.path.exists(optimization_results_file):
        print(f"❌ Results file not found: {optimization_results_file}")
        return False

    with open(optimization_results_file, "r") as f:
        results = json.load(f)

    params = results["parameters"]
    fitness = results["optimization_results"]["best_fitness"]

    print(f"📊 Found optimization results with fitness: {fitness:.3f}")
    print(f"   Positions: {params['num_positions']}")
    print(f"   Diameter: {params['outer_diameter_mm']:.1f}mm")
    print(f"   Arc angle: {params['arc_angle_deg']:.1f}°")

    # Generate the updated parameters.py content
    new_content = f'''"""
Parameter definitions and validation for the rudder encoder disk.

This module contains all configurable parameters and validation functions
to ensure the design meets manufacturing and functional constraints.

Note: Default parameters have been optimized using genetic algorithm.
Optimization fitness: {fitness:.3f}
"""

import math
from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class EncoderParameters:
    """Complete parameter set for encoder disk generation."""
    
    # Physical dimensions (mm) - OPTIMIZED
    outer_diameter_mm: float = {params['outer_diameter_mm']:.1f}
    inner_diameter_mm: float = {params['inner_diameter_mm']:.1f}
    disk_thickness_mm: float = {params['disk_thickness_mm']:.1f}
    
    # Arc specifications - OPTIMIZED
    arc_angle_deg: float = {params['arc_angle_deg']:.1f}
    
    # Encoding parameters - OPTIMIZED
    num_positions: int = {params['num_positions']}
    num_tracks: int = {params['num_tracks']}
    
    # Track layout - OPTIMIZED
    track_width_mm: float = {params['track_width_mm']:.1f}
    track_spacing_mm: float = {params['track_spacing_mm']:.1f}
    gap_width_deg: float = {params['gap_width_deg']:.1f}
    
    # Limit switch bumpers - OPTIMIZED
    bump_extension_mm: float = {params['bump_extension_mm']:.1f}
    bump_width_deg: float = {params['bump_width_deg']:.1f}
    
    # Manufacturing constraints
    min_feature_size_mm: float = 0.4  # Typical nozzle diameter
    min_gap_size_mm: float = 0.5      # Reliable printing minimum
    min_wall_thickness_mm: float = 1.2 # 3 perimeters
    
    @property
    def radius_outer(self) -> float:
        """Outer radius in mm."""
        return self.outer_diameter_mm / 2
    
    @property
    def radius_inner(self) -> float:
        """Inner radius in mm."""
        return self.inner_diameter_mm / 2
    
    @property
    def angular_resolution_deg(self) -> float:
        """Angular resolution per position in degrees."""
        return self.arc_angle_deg / self.num_positions
    
    @property
    def track_pitch_mm(self) -> float:
        """Distance between track centers."""
        return self.track_width_mm + self.track_spacing_mm
    
    @property
    def required_bits(self) -> int:
        """Number of bits required for encoding positions."""
        return math.ceil(math.log2(self.num_positions))
    
    @property
    def usable_radius_mm(self) -> float:
        """Available radius for tracks."""
        return self.radius_outer - self.radius_inner


# Keep the rest of the original file content...
class ParameterValidator:
    """Validates encoder parameters against manufacturing and functional constraints."""
    
    def __init__(self, params: EncoderParameters):
        self.params = params
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Perform complete parameter validation.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors.clear()
        self.warnings.clear()
        
        self._validate_basic_geometry()
        self._validate_encoding_parameters()
        self._validate_manufacturing_constraints()
        self._validate_track_layout()
        self._validate_optical_requirements()
        
        return len(self.errors) == 0, self.errors.copy(), self.warnings.copy()
    
    def _validate_basic_geometry(self):
        """Validate basic geometric parameters."""
        if self.params.outer_diameter_mm <= self.params.inner_diameter_mm:
            self.errors.append("Outer diameter must be greater than inner diameter")
        
        if self.params.disk_thickness_mm < self.params.min_wall_thickness_mm:
            self.errors.append(f"Disk thickness {{self.params.disk_thickness_mm}}mm "
                             f"less than minimum {{self.params.min_wall_thickness_mm}}mm")
        
        if self.params.arc_angle_deg <= 0 or self.params.arc_angle_deg > 360:
            self.errors.append("Arc angle must be between 0 and 360 degrees")
        
        if self.params.usable_radius_mm <= 0:
            self.errors.append("No usable radius available for tracks")
    
    def _validate_encoding_parameters(self):
        """Validate Gray code encoding parameters."""
        if self.params.num_positions <= 0:
            self.errors.append("Number of positions must be positive")
        
        if self.params.num_tracks != self.params.required_bits:
            self.errors.append(f"Track count {{self.params.num_tracks}} doesn't match "
                             f"required bits {{self.params.required_bits}} for "
                             f"{{self.params.num_positions}} positions")
        
        if not (self.params.num_positions & (self.params.num_positions - 1)) == 0:
            self.warnings.append(f"Position count {{self.params.num_positions}} is not "
                               f"a power of 2, some Gray codes will be unused")
    
    def _validate_manufacturing_constraints(self):
        """Validate 3D printing constraints."""
        # Calculate minimum gap size at outer radius
        min_gap_size_mm = (self.params.gap_width_deg * math.pi * 
                          self.params.radius_outer) / 180
        
        if min_gap_size_mm < self.params.min_gap_size_mm:
            self.errors.append(f"Gap size {{min_gap_size_mm:.2f}}mm at outer radius "
                             f"less than minimum {{self.params.min_gap_size_mm}}mm")
        
        if self.params.track_width_mm < self.params.min_wall_thickness_mm:
            self.errors.append(f"Track width {{self.params.track_width_mm}}mm "
                             f"less than minimum wall thickness "
                             f"{{self.params.min_wall_thickness_mm}}mm")
        
        if self.params.track_spacing_mm < self.params.min_feature_size_mm:
            self.warnings.append(f"Track spacing {{self.params.track_spacing_mm}}mm "
                               f"may be difficult to print reliably")
    
    def _validate_track_layout(self):
        """Validate track layout fits within available space."""
        total_track_space = (self.params.num_tracks * self.params.track_width_mm + 
                           (self.params.num_tracks - 1) * self.params.track_spacing_mm)
        
        if total_track_space > self.params.usable_radius_mm:
            self.errors.append(f"Total track space {{total_track_space:.1f}}mm "
                             f"exceeds available radius {{self.params.usable_radius_mm:.1f}}mm")
        
        # Check if outermost track fits
        outermost_radius = (self.params.radius_inner + 
                          (self.params.num_tracks - 1) * self.params.track_pitch_mm + 
                          self.params.track_width_mm)
        
        if outermost_radius > self.params.radius_outer:
            self.errors.append(f"Outermost track extends beyond disk edge")
    
    def _validate_optical_requirements(self):
        """Validate optical sensing requirements."""
        if self.params.angular_resolution_deg < 0.5:
            self.warnings.append(f"Angular resolution {{self.params.angular_resolution_deg:.2f}}° "
                               f"may be too fine for reliable optical sensing")
        
        if self.params.track_spacing_mm < 1.0:
            self.warnings.append("Track spacing may be too tight for optical sensor array")


def create_default_parameters() -> EncoderParameters:
    """Create default parameter set optimized via genetic algorithm."""
    return EncoderParameters()


def create_high_resolution_parameters() -> EncoderParameters:
    """Create parameters for higher resolution encoding."""
    params = EncoderParameters()
    params.num_positions = 64
    params.num_tracks = 6  # 6 bits for 64 positions
    params.outer_diameter_mm = 120  # Larger disk for more tracks
    params.gap_width_deg = 1.5  # Adjust for manufacturability
    return params


def create_compact_parameters() -> EncoderParameters:
    """Create parameters for compact installation."""
    params = EncoderParameters()
    params.num_positions = 8
    params.num_tracks = 3  # 3 bits for 8 positions
    params.outer_diameter_mm = 70  # Smaller disk
    params.track_width_mm = 5.0  # Adjust for fewer tracks
    return params
'''

    # Write to parameters.py
    params_file = os.path.join(os.path.dirname(__file__), "utils", "parameters.py")

    # Backup original
    backup_file = params_file + ".backup"
    if os.path.exists(params_file) and not os.path.exists(backup_file):
        import shutil

        shutil.copy2(params_file, backup_file)
        print(f"📋 Original parameters backed up to {backup_file}")

    # Write optimized parameters
    with open(params_file, "w") as f:
        f.write(new_content)

    print(f"✅ Updated default parameters in {params_file}")
    print("🔄 Run 'make validate' to test the optimized parameters")

    return True


def main():
    """Main application routine."""
    print("🔧 Parameter Optimization Applier")
    print("=" * 40)

    # Default results file
    results_file = os.path.join(
        os.path.dirname(__file__), "..", "output", "optimized_parameters.json"
    )

    # Allow custom results file
    if len(sys.argv) > 1:
        results_file = sys.argv[1]

    success = update_default_parameters(results_file)

    if success:
        print("\n🎉 Parameters updated successfully!")
        print("Next steps:")
        print("  1. Run 'make validate' to test the new parameters")
        print("  2. Run 'make generate' to create the optimized encoder")
        print("  3. If issues occur, restore from .backup file")
    else:
        print("\n❌ Failed to update parameters")
        print("Make sure to run 'make optimize' first to generate results")


if __name__ == "__main__":
    main()
