# Gray Code Optical Encoder Disk Generator

Generates 3D-printable optical encoder disks using Gray code for absolute position sensing. Outputs OpenSCAD files for FDM fabrication.

Discussion regarding this projecrt can be found on https://Susannecoates.com:
1. https://susannecoates.com/building-a-custom-optical-encoder-for-rudder-position-sensing-part-1/
2. https://susannecoates.com/building-a-custom-optical-encoder-for-rudder-position-sensing-part-2/

## Requirements

- Python 3.8+
- Poetry (dependency management)
- OpenSCAD (for STL export, optional)

## Installation

```bash
curl -sSL https://install.python-poetry.org | python3 -
poetry install
```

## Basic Usage

Generate encoder with default parameters (32 positions, 5-bit Gray code):

```bash
poetry run python src/encoder_generator.py
```

Output: `output/default_encoder.scad`

## Command Line Options

```bash
# Use predefined configuration
poetry run python src/encoder_generator.py --config [default|high_res|compact]

# Specify output file
poetry run python src/encoder_generator.py --output path/to/file.scad

# Validate parameters without generating
poetry run python src/encoder_generator.py --validate --info

# Export pattern data
poetry run python src/encoder_generator.py --export-data output/patterns.json

# Generate without limit switch bumpers
poetry run python src/encoder_generator.py --no-bumpers

# Custom parameters from JSON
poetry run python src/encoder_generator.py --config custom --params config.json
```

## Predefined Configurations

| Configuration | Positions | Bits | Outer Diameter | Inner Diameter | Arc Angle |
|---------------|-----------|------|----------------|----------------|-----------|
| default       | 32        | 5    | 116.2mm       | 35.6mm         | 57.1°     |
| high_res      | 64        | 6    | 120mm         | 30mm           | 360°      |
| compact       | 16        | 4    | 80mm          | 20mm           | 90°       |

Default parameters derived from genetic algorithm optimisation (fitness: 1.115).

## Custom Configuration

Create JSON file with parameters:

```json
{
  "outer_diameter_mm": 100.0,
  "inner_diameter_mm": 30.0,
  "disk_thickness_mm": 3.0,
  "arc_angle_deg": 90.0,
  "num_positions": 32,
  "num_tracks": 5,
  "track_width_mm": 3.5,
  "track_spacing_mm": 1.5,
  "gap_width_deg": 2.5,
  "bump_extension_mm": 5.0,
  "bump_width_deg": 3.0
}
```

## Genetic Algorithm Optimisation

Optimise parameters for specific constraints:

```bash
poetry run python src/genetic_optimizer.py
```

Edit `genetic_optimizer.py` to specify fixed parameters and optimisation goals. Algorithm runs 50 generations by default, outputs results to `output/optimized_parameters.json`.

## Validation System

Three-layer validation:
1. Geometric constraints (radii, angles, track fitting)
2. Gray code correctness (single-bit transitions, pattern validity)
3. Printability analysis (minimum feature sizes, gap widths, manufacturing constraints)

## Manufacturing Constraints

- Minimum feature size: 0.4mm (standard nozzle) or 0.16mm (precision nozzle)
- Minimum gap width: 0.5mm
- Minimum wall thickness: 1.2mm (3 perimeters at 0.4mm line width)
- Track spacing: ≥ 0.5mm for reliable separation

## 3D Printing Parameters

Recommended settings for FDM:
- Layer height: 0.2mm
- Perimeters: 3
- Infill: 20%
- Print orientation: cutouts facing build plate
- Materials: PETG, ASA (UV resistant), PLA (indoor use)

## Development

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Code formatting
poetry run black src/ tests/

# Type checking
poetry run mypy src/

# Linting
poetry run flake8 src/ tests/
```

Or use Makefile commands:

```bash
make test           # Run test suite
make test-coverage  # Generate coverage report
make format         # Format code
make lint           # Check code style
make type-check     # Run type checker
make check-all      # Run all quality checks
```

## File Structure

```
gray-encoder-disk-generator/
├── src/
│   ├── encoder_generator.py      # Main CLI
│   ├── genetic_optimizer.py      # GA optimisation
│   ├── apply_optimization.py     # Apply GA results
│   ├── gui_encoder_controller.py # PyQt6 GUI (optional)
│   ├── gray_code/
│   │   ├── converter.py          # Gray code mathematics
│   │   └── validator.py          # Pattern validation
│   ├── geometry/
│   │   ├── arc_utils.py          # Geometric primitives
│   │   ├── track_generator.py    # Track pattern generation
│   │   └── assembly.py           # Disk assembly
│   └── utils/
│       ├── parameters.py         # Parameter definitions
│       └── printer_constraints.py # Printability analysis
├── tests/                         # Test suite
├── output/                        # Generated SCAD/JSON files
└── docs/
    └── ARCHITECTURE.md            # Technical documentation
```

## Architecture

System consists of five main components:

1. **Gray code module** (`gray_code/`): Mathematical operations for Gray code generation, bit extraction, sequence validation, pattern analysis.

2. **Geometry module** (`geometry/`): 3D solid generation using SolidPython, arc sector primitives, Boolean operations for disk assembly.

3. **Parameter system** (`utils/`): Parameter validation, printability analysis, constraint checking.

4. **Genetic optimiser** (`genetic_optimizer.py`): Multi-objective fitness function, tournament selection, constrained optimisation.

5. **Generation pipeline** (`encoder_generator.py`): Parameter loading, validation orchestration, geometry generation, OpenSCAD export.

See `docs/ARCHITECTURE.md` for detailed technical documentation.

## Troubleshooting

**Validation errors**: Run with `--validate --info` to see detailed constraint violations.

**Gap size too small**: Increase `gap_width_deg`, reduce `num_positions`, or increase `outer_diameter_mm`.

**Track count mismatch**: Ensure `num_tracks = ceil(log2(num_positions))`.

**Printability warnings**: Check feature sizes against nozzle diameter. Use `PrintabilityAnalyzer` output for specific recommendations.

## License
MIT License. See LICENSE file for details.
