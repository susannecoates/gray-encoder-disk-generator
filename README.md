# Rudder Encoder Disk Generator

A complete system for generating 3D printable optical encoder disks for sailboat rudder position sensing using Gray code absolute positioning.

## 🖥️ GUI Interface (Recommended)

Launch the user-friendly graphical interface:

```bash
# Using Poetry
poetry run python src/gui_encoder_controller.py

# OR using make
make gui

# OR using the launcher
python launch_gui.py
```

The GUI provides:
- **Interactive parameter control** with real-time validation
- **Physical dimension inputs** (inner radius, encoder width, arc angle)
- **Genetic algorithm optimization** with progress tracking
- **One-click generation** of SCAD files
- **Built-in validation** and parameter checking

## Quick Start (Command Line)

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install Dependencies**:
   ```bash
   poetry install
   ```

3. **Generate Default Encoder**:
   ```bash
   poetry run python src/encoder_generator.py
   # OR using make
   make generate
   ```

4. **Output**: `output/default_encoder.scad` - Open in OpenSCAD to render and export STL

## Features

- **Absolute Position Encoding**: No homing required - position known immediately on power-up
- **Gray Code Pattern**: Single-bit transitions between positions eliminate read errors
- **3D Printable**: Optimized for FDM printing with standard nozzles
- **Marine Ready**: Designed for harsh marine environments
- **Configurable**: Multiple predefined configurations plus custom parameters
- **Validated**: Comprehensive parameter and design validation

## Configurations

### Default Configuration
- 32 positions (5-bit Gray code)
- 100mm outer diameter, 30mm inner diameter
- 30° arc angle
- Optimized for reliable 3D printing

### High Resolution
- 64 positions (6-bit Gray code)  
- 120mm outer diameter
- Higher precision for demanding applications

### Compact
- 16 positions (4-bit Gray code)
- 80mm outer diameter
- Space-constrained installations

## Usage Examples

```bash
# Generate high resolution encoder
poetry run python src/encoder_generator.py --config high_res --output output/high_res_encoder.scad
# OR using make
make run-high-res

# Validate design without generating
poetry run python src/encoder_generator.py --validate --info
# OR using make
make validate

# Generate without limit switch bumpers
poetry run python src/encoder_generator.py --no-bumpers --output output/no_bumpers_encoder.scad

# Export pattern data for analysis
poetry run python src/encoder_generator.py --export-data output/patterns.json
# OR using make
make export-data

# Verbose output
poetry run python src/encoder_generator.py --verbose --info
# OR using make
make run-validate
```

## Development Commands

Using Poetry and Make for common tasks:

```bash
# Development setup
make dev-setup              # Install dependencies and dev tools

# Code quality
make lint                   # Check code style
make format                 # Format code
make type-check            # Run type checking
make test                  # Run tests
make test-coverage         # Run tests with coverage
make check-all             # Run all quality checks

# Generation commands
make generate              # Generate default encoder
make generate-all          # Generate all configurations
make validate              # Validate default design
make export-data           # Export pattern data
make clean                 # Clean generated files

# Quick shortcuts
make run-default           # Quick default generation
make run-validate          # Quick validation with info
make run-high-res          # Generate high resolution
make run-compact           # Generate compact version
```

## Design Validation

The generator includes comprehensive validation:

- **Parameter Validation**: Geometric constraints, encoding efficiency
- **Gray Code Validation**: Proper single-bit transitions, pattern analysis  
- **Printability Analysis**: Feature sizes, manufacturing constraints
- **Assembly Validation**: Component interference, structural integrity

## File Structure

```
rudder-encoder/
├── ARCHITECTURE.md          # Detailed design documentation
├── README.md                # This file
├── pyproject.toml           # Poetry configuration
├── Makefile                 # Development commands
├── .gitignore               # Git ignore patterns
├── src/                     # Source code
│   ├── encoder_generator.py # Main generator script
│   ├── utils/               # Parameter management
│   ├── gray_code/           # Gray code mathematics
│   └── geometry/            # 3D geometry generation
├── tests/                   # Test suite
├── output/                  # Generated files (.scad, .json)
└── docs/                    # Additional documentation
```

## Gray Code Advantages

1. **Error Tolerance**: Only one bit changes between adjacent positions
2. **Noise Immunity**: Single-bit errors don't propagate  
3. **No Invalid States**: All transitions are valid
4. **Absolute Positioning**: No reference position required

## 3D Printing Guidelines

### Recommended Settings
- **Layer Height**: 0.2mm
- **Perimeters**: 3 (for strength)
- **Infill**: 20%
- **Speed**: 50mm/s perimeters, 100mm/s infill
- **Material**: PETG or ASA (UV resistant)

### Print Orientation
- Print with cutouts facing down for best edge quality
- No supports required with proper design
- Use brim for bed adhesion on large disks

## Testing

Run the test suite using Poetry:

```bash
# Run all tests
make test
# OR
poetry run pytest

# Run with coverage
make test-coverage
# OR  
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_gray_code.py -v

# Run with verbose output
poetry run pytest tests/ -v
```

Tests cover:
- Gray code mathematics
- Geometry calculations  
- Parameter validation
- Assembly verification

## Code Quality

The project includes comprehensive code quality tools:

```bash
# Check code style
make lint

# Format code automatically
make format

# Type checking
make type-check

# Run all quality checks
make check-all
```

## Troubleshooting

### Common Issues

**"Gap size too small" error**:
- Increase `gap_width_deg` parameter
- Reduce number of positions
- Use larger outer diameter

**"Track count mismatch" error**:
- Ensure `num_tracks` matches required bits for `num_positions`
- Use power-of-2 position counts for efficiency

**Printability warnings**:
- Check minimum feature sizes
- Verify track spacing
- Consider material capabilities

### Parameter Tuning

The system is designed to guide you toward printable designs:

1. Start with a predefined configuration
2. Use `--validate --info` to check constraints
3. Adjust parameters based on validation feedback
4. Test print a small section first

## Integration

### Optical Sensor Setup
- Position sensors radially aligned with tracks
- Use IR LED/photodiode pairs for contrast
- Ensure sensor spacing matches track pitch
- Calibrate sensor thresholds for reliable readings

### Mechanical Mounting
- Design sensor housing to maintain precise alignment
- Allow for thermal expansion
- Protect sensors from marine environment
- Consider shock/vibration isolation

## Support

For issues or questions:
1. Check validation output for guidance
2. Review ARCHITECTURE.md for detailed technical information
3. Run tests to verify installation
4. Examine generated .scad file in OpenSCAD

## License

This project is designed for educational and practical use in marine applications. Please follow safe engineering practices when implementing position-critical systems.
