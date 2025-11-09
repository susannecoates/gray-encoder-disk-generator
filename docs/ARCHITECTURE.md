# Architecture Documentation

## Project Overview

This system generates parametric Gray code optical encoder disks for rudder position sensing in marine applications. The design produces 3D-printable encoder geometries using SolidPython to generate OpenSCAD files. Encoding is optimised for accurate position tracking within the spatial constraints of sailboat rudder installations.

## Design Philosophy

### Module Organisation

**Separation of Concerns**:
- `gray_code/` - Gray code mathematics and validation
- `geometry/` - 3D shape generation
- `utils/` - Parameter management and constraints
- `genetic_optimizer.py` - Optimisation engine
- User interfaces decoupled from core logic

**Validation Strategy**:
- Parameters validated before geometry generation
- Gray code patterns validated for correctness
- Manufacturing constraints checked before export
- Assembly validated before SCAD generation

**Configuration System**:
- Default parameters in `parameters.py`
- Predefined configurations (default, high_res, compact)
- User-customisable JSON configurations

**Interface Options**:
- CLI for automation and scripting
- GUI for interactive design
- Makefile for common operations
- Python API for programmatic use

### Technical Constraints

**Absolute Positioning**: No homing or initialisation required. Position is immediately known on power-up.

**Marine Environment**: Design accounts for vibration, moisture, and electrical noise.

**3D Printing**: Manufacturable with standard FDM printers.

**Optical Sensing**: Non-contact sensing eliminates wear.

### Gray Code Properties

Gray code ensures only one bit changes between adjacent positions:
- Single-bit changes reduce error propagation
- No transient invalid states during transitions
- Mechanical misalignment affects only one bit
- Enhanced noise immunity compared to binary encoding

---

## Mathematical Foundation

### Gray Code Theory

#### Binary to Gray Code Conversion
```
Gray(n) = n XOR (n >> 1)
```

#### Gray Code Bit Extraction
For an n-bit Gray code representing position `pos`:
```python
def gray_code_bits(pos, num_bits):
    gray_value = pos ^ (pos >> 1)
    return [(gray_value >> i) & 1 for i in range(num_bits)]
```
Returns bits as `[LSB, ..., MSB]`. LSB corresponds to innermost track, MSB to outermost track.

#### Position Resolution Calculations
- **Angular Resolution**: `arc_angle_degrees / num_positions`
- **Minimum Gap Size**: `(angular_resolution × π × radius) / 180°`
- **Track Width**: `(outer_radius - inner_radius) / num_tracks`

### Geometric Constraints

#### 3D Printing Limitations
- **Minimum Feature Size**: 0.4mm (standard nozzle diameter)
- **Minimum Gap Width**: 0.5mm for reliable printing
- **Minimum Wall Thickness**: 1.2mm (3 perimeters × 0.4mm line width)
- **Layer Height**: Minimum 0.2mm for layer adhesion

Note: Code comments reference 0.16mm capability for high-precision printers. Current parameters use 0.4mm constraints.

#### Optical Sensing Requirements
- **Gap Width**: Optimised to 2.8° (provides ~2.84mm at outer radius)
- **Track Pitch**: 3.8mm (3.3mm track width + 0.5mm spacing)
- **Sensor Alignment**: Multiple sensors positioned radially to read each track

### Design Specifications

**Current Optimised Parameters**:
- Positions: 32 (5-bit Gray code)
- Outer Diameter: 116.2mm
- Inner Diameter: 20mm
- Disk Thickness: 2.3mm
- Arc Angle: 57.1°
- Track Width: 3.3mm
- Track Spacing: 0.5mm
- Gap Width: 2.8°
- Limit Switch Bumpers: 5.8mm extension, 3.0° width
- Optimisation Fitness: 1.115 (50 generations, population 30-50)

**Angular Resolution**: 1.78° per position (32 positions across 57.1° arc)

---

## Implementation Architecture

### 1. Parameter Management (`utils/`)

```python
# parameters.py - Parameter definitions
@dataclass
class EncoderParameters:
    """Complete parameter set for encoder generation"""
    num_positions: int = 32
    outer_diameter_mm: float = 116.2
    inner_diameter_mm: float = 20.0
    disk_thickness_mm: float = 2.3
    arc_angle_deg: float = 57.1
    track_width_mm: float = 3.3
    track_spacing_mm: float = 0.5
    gap_width_deg: float = 2.8
    # ... additional parameters

class ParameterValidator:
    """Multi-layer validation of all parameters"""
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        # Basic geometry checks
        # Encoding parameter validation
        # Manufacturing constraints
        # Track layout fitting
        # Optical sensing requirements
```

### 2. Geometry Generation (`geometry/`)

```python
# arc_utils.py - Geometric primitives
def create_arc_sector(inner_r, outer_r, start_deg, end_deg, height, segments=50):
    """Generate 3D SolidPython arc sector objects"""
    points = create_sector_points(...)
    return linear_extrude(height)(polygon(points))

# track_generator.py - Gray code track patterns
class TrackGenerator:
    def generate_all_tracks(self) -> List[List[int]]:
        """Generate Gray code patterns for all tracks"""
        
    def generate_track_cutouts(self, track_idx: int) -> List[Any]:
        """Create 3D cutout objects for specific track"""
        # Handles consecutive position runs efficiently
        # Adds overlap for clean cuts

# assembly.py - Final disk assembly
class EncoderAssembler:
    def assemble_complete_disk(self, include_bumpers=True) -> Any:
        """Combine all components into final SolidPython geometry"""
        # Base disk (arc sector)
        # Track cutouts (union of all patterns)
        # Limit switch bumpers (at 0° and arc_angle_deg)
        # Optional mounting holes
```

### 3. Gray Code Engine (`gray_code/`)

```python
# converter.py - Core Gray code mathematics
def binary_to_gray(n: int) -> int:
    """n XOR (n >> 1)"""
    
def gray_code_bits(position: int, num_bits: int) -> List[int]:
    """Extract bit pattern for specific position"""
    
def extract_track_pattern(track_idx: int, num_positions: int, num_bits: int):
    """Extract binary pattern for entire track across all positions"""
    
def analyze_track_transitions(pattern: List[int]) -> dict:
    """Analyse run lengths, transitions, balance"""

# validator.py - Pattern validation
class GrayCodeValidator:
    def validate_encoder_pattern(self, num_positions, num_tracks):
        """Comprehensive validation with errors/warnings/info"""
        # Sequence validation (single-bit transitions)
        # Track pattern analysis
        # Encoding efficiency
        # Physical constraint checking
```

### 4. Genetic Optimiser (`genetic_optimizer.py`)

```python
class ParameterGenome:
    """Parameter set as genome for genetic algorithm"""
    def mutate(self, mutation_rate=0.1, fixed_params=None):
        """±20% bounded mutation, respects fixed parameters"""
        
    def crossover(self, other):
        """Uniform parameter crossover"""

class EncoderOptimizer:
    """Multi-objective genetic algorithm optimiser"""
    def evaluate_fitness(self, genome) -> float:
        """Weighted fitness scoring:
        - Printability (40%)
        - Resolution (20%)
        - Encoding efficiency (20%)
        - Size optimisation (10%)
        - Manufacturability (10%)
        """
    
    def optimize(self, generations=100, population_size=50):
        """Tournament selection + elitism + full exploration"""
        # Runs all generations for thorough solution space exploration
        # No early stopping for best results
```

### 5. User Interfaces

**CLI Interface** (`encoder_generator.py`):
```bash
# Command-line tool with multiple modes
--config [default|high_res|compact|custom]
--validate, --info, --export-data
--no-bumpers, --verbose
```

**GUI Interface** (`gui_encoder_controller.py`):
```python
class EncoderControllerGUI(QMainWindow):
    """PyQt6 GUI with:
    - Real-time parameter editing
    - Background optimisation worker threads
    - Validation and generation
    - Results visualisation
    """
```

**Build System** (`Makefile`):
```bash
make validate        # Validate design
make generate        # Generate SCAD
make optimize        # Run GA optimisation
make apply-optimization  # Update defaults with results
make gui            # Launch GUI
make test           # Run test suite
```

---

## File Structure

```
gray-encoder-disk-generator/
├── pyproject.toml           # Poetry configuration
├── Makefile                 # Build automation
├── launch_gui.py            # GUI launcher script
├── src/
│   ├── encoder_generator.py      # Main CLI generation script
│   ├── genetic_optimizer.py      # GA optimisation engine
│   ├── apply_optimization.py     # Apply optimised parameters
│   ├── gui_encoder_controller.py # PyQt6 GUI interface
│   ├── geometry/
│   │   ├── __init__.py
│   │   ├── arc_utils.py          # Arc and sector geometry primitives
│   │   ├── track_generator.py    # Gray code track pattern generation
│   │   └── assembly.py           # Final disk assembly logic
│   ├── gray_code/
│   │   ├── __init__.py
│   │   ├── converter.py          # Gray code mathematics & conversions
│   │   └── validator.py          # Pattern validation & analysis
│   └── utils/
│       ├── __init__.py
│       ├── parameters.py         # Parameter definitions & validation
│       └── printer_constraints.py # 3D printing limitations & analysis
├── tests/
│   ├── test_gray_code.py
│   ├── test_geometry.py
│   └── test_assembly.py
├── output/                   # Generated files
│   ├── *.scad               # OpenSCAD files
│   ├── *.json               # Pattern data & optimisation results
│   └── optimized_parameters.json # GA results
└── docs/
    ├── ARCHITECTURE.md       # This document
    └── FIX_SUMMARY.md       # Recent corrections
```

---

## Data Flow and Generation Pipeline

### Standard Generation Workflow

1. **Parameter Loading**: Load from defaults or JSON configuration
2. **Parameter Validation**: `ParameterValidator.validate_all()`
3. **Gray Code Validation**: `GrayCodeValidator.validate_encoder_pattern()`
4. **Printability Analysis**: `PrintabilityAnalyzer` checks manufacturing constraints
5. **Track Pattern Generation**: `TrackGenerator.generate_all_tracks()`
6. **Cutout Generation**: `TrackGenerator.generate_track_cutouts()`
7. **Assembly**: `EncoderAssembler.assemble_complete_disk()`
8. **Assembly Validation**: Check final geometry
9. **OpenSCAD Generation**: `scad_render()` converts SolidPython to SCAD
10. **File Output**: Write `.scad` file

### Key Data Transformations

**Parameters → Gray Code Patterns**:
```python
positions = 32  # User input
tracks = 5      # Computed: ceil(log2(32)) = 5

# For each position (0-31):
binary_position = position          # e.g., 5 = 0b00101
gray_code = binary_position ^ (binary_position >> 1)  # 0b00111

# Extract bits for each track (LSB to MSB):
track_patterns = [
    [bit_0 for position in positions],  # Innermost track (LSB)
    [bit_1 for position in positions],
    ...
    [bit_4 for position in positions]   # Outermost track (MSB)
]
```

**Track Patterns → 3D Cutouts**:
```python
for track_idx, pattern in enumerate(track_patterns):
    # Calculate track radii (inner to outer)
    track_inner_radius = inner_radius + (track_idx * track_pitch)
    track_outer_radius = track_inner_radius + track_width
    
    # Find runs of ones (cutouts for transmissive encoder)
    for run_start, run_length in find_one_runs(pattern):
        start_angle = run_start * angular_resolution
        end_angle = start_angle + (run_length * angular_resolution)
        
        # Create arc sector cutout
        cutout = create_arc_sector(
            track_inner_radius, 
            track_outer_radius,
            start_angle, 
            end_angle,
            height=disk_thickness + 2  # Ensure through-cut
        )
```

**Components → Final Assembly**:
```python
# Solid components (union)
base_disk = create_full_arc_disk(inner_r, outer_r, arc_angle, thickness)
bumper_start = create_bumper_at_angle(0°)
bumper_end = create_bumper_at_angle(arc_angle)
solid_parts = union(base_disk, bumper_start, bumper_end)

# Cutout components (union)
all_cutouts = union(*[cutout for cutout in track_cutouts])

# Final disk (difference)
encoder_disk = difference(solid_parts, all_cutouts)
```

**SolidPython → OpenSCAD**:
```python
# SolidPython generates OpenSCAD code
scad_code = scad_render(encoder_disk)

# Write to file with header
with open('encoder_disk.scad', 'w') as f:
    f.write(header_comment)
    f.write(scad_code)
```

### File Output Formats

**SCAD Output** (`*.scad`):
```openscad
// Rudder Encoder Disk
// Generated by encoder_generator.py
// Parameters: 32 positions, 5 tracks, 57.1° arc

union() {
  difference() {
    // Base disk
    linear_extrude(height=2.3) {
      polygon(points=[[...], ...]);  // Arc sector points
    }
    // Track cutouts
    union() {
      linear_extrude(height=4.3) {
        polygon(points=[[...], ...]);  // Cutout patterns
      }
    }
  }
  // Limit bumpers
  translate([...]) { cube([5.8, 3.0, 2.3]); }
}
```

**JSON Pattern Export** (`*.json`):
```json
{
  "metadata": {
    "generator": "encoder_generator.py",
    "version": "1.0.0"
  },
  "parameters": {
    "num_positions": 32,
    "num_tracks": 5,
    "track_width_mm": 3.3,
    ...
  },
  "pattern_data": {
    "gray_sequence": [0, 1, 3, 2, 6, 7, 5, 4, ...],
    "track_patterns": {
      "track_0": [0, 0, 1, 1, 1, 1, 0, 0, ...],
      "track_1": [0, 1, 1, 0, 1, 1, 1, 0, ...],
      ...
    },
    "transition_analysis": {
      "track_0": {
        "transitions": 8,
        "zero_runs": [2, 2],
        "one_runs": [4]
      },
      ...
    }
  }
}
```

---

## Optimisation Workflow

### Genetic Algorithm Design

The genetic algorithm optimiser finds optimal track layout parameters whilst respecting fixed physical and encoding constraints.

#### Optimisation Strategy

**Fixed Parameters** (User Requirements):
- Physical dimensions: `outer_diameter_mm`, `inner_diameter_mm`, `disk_thickness_mm`
- Encoding specifications: `num_positions`, `num_tracks`, `arc_angle_deg`
- Bumper dimensions: `bump_extension_mm`, `bump_width_deg`
- Manufacturing limits: `min_feature_size_mm`, `min_gap_size_mm`, `min_wall_thickness_mm`

**Optimisable Parameters** (Track Layout):
- `track_width_mm` - Width of each track (0.5mm - 8.0mm range)
- `track_spacing_mm` - Spacing between tracks (0.2mm - 3.0mm range)
- `gap_width_deg` - Angular gap width (0.3° - 6.0° range)

#### Fitness Function Components

```python
# Weighted multi-objective fitness
total_fitness = (
    0.40 * printability_score    # Can it be printed?
  + 0.20 * resolution_score      # Meets position requirements?
  + 0.20 * efficiency_score      # Good Gray code utilisation?
  + 0.10 * size_score           # Close to target diameter?
  + 0.10 * manufacturability_score  # Easy to produce?
)

# Bonus for fully valid designs
if all_validations_pass:
    total_fitness *= 1.2
```

**Component Scoring**:
1. **Printability** (40%): Parameter validation + feature size checks
2. **Resolution** (20%): Position count within target range (16-64 default)
3. **Efficiency** (20%): `num_positions / 2^num_tracks` ratio
4. **Size** (10%): Distance from target outer diameter
5. **Manufacturability** (10%): Track count, dimension reasonableness

#### Algorithm Configuration

```python
# Default settings
generations = 50              # Full exploration, no early stopping
population_size = 30         # Adequate diversity
tournament_size = 5          # Selection pressure
elite_size = 10%             # Preserve best solutions
mutation_rate = 10%          # Per-genome mutation probability
mutation_range = ±20%        # Change magnitude
```

**Algorithm Properties**:
- **No early stopping**: Runs all generations for thorough exploration
- **Tournament selection**: Balances selection pressure and diversity
- **Elitism**: Prevents losing best solutions
- **Bounded mutation**: Prevents invalid parameter combinations
- **Uniform crossover**: Explores parameter combinations independently

#### Typical Optimisation Run

```bash
make optimize
# Runs 50 generations × 30 population = 1500 evaluations
# Takes ~5-10 minutes on modern hardware
# Outputs: output/optimized_parameters.json
# Best fitness typically: 1.0 - 1.2

make apply-optimization
# Updates src/utils/parameters.py with optimised values
# Creates backup: parameters.py.backup

make generate
# Creates SCAD file with optimised parameters
```

#### Convergence Behaviour

Typical fitness evolution:
```
Generation 1:  Best=0.421, Avg=0.234  (many invalid genomes)
Generation 10: Best=0.876, Avg=0.654  (improving fitness)
Generation 20: Best=1.023, Avg=0.832  (first valid designs)
Generation 30: Best=1.115, Avg=0.947  (converging)
Generation 50: Best=1.115, Avg=1.034  (stable solution)
```

Stagnation detection monitors improvement but doesn't stop early - continues exploring for potentially better solutions.

#### Customising Optimisation

**Via Code** (`genetic_optimizer.py`):
```python
# Modify optimisation goals
goals = OptimizationGoals(
    min_positions=64,           # Require higher resolution
    max_positions=128,
    target_outer_diameter=120,  # Larger disk
    weight_printability=0.5,    # Prioritise printability
    weight_resolution=0.3,      # Higher resolution importance
)
```

**Via GUI**:
- Set desired parameters in GUI
- Click "Optimize" button
- Monitor progress in real-time
- Apply results automatically

---

## Technical Constraints and Solutions

### 3D Printing Challenges

**Small Feature Sizes**:
- Issue: Sub-millimetre gaps difficult to print reliably
- Solution: Minimum 0.5mm gap width, validated in parameter checking

**Overhangs and Bridges**:
- Issue: Cutouts may create unsupported geometry
- Solution: Ensure all cutouts are through-holes with minimal bridging

**Layer Adhesion**:
- Issue: Thin walls may delaminate
- Solution: Minimum 1.2mm wall thickness (3 perimeters × 0.4mm)

### Optical Sensing Considerations

**Sensor Alignment**:
- Multiple sensors positioned radially to read each track
- Sensor spacing must match track pitch exactly
- Allowance for mechanical tolerance in mounting

**Light Path Optimisation**:
- Clean edge transitions for sharp optical contrast
- Sufficient gap width for LED/photodiode pairs
- Consider IR wavelengths for improved contrast

### Marine Environment Adaptations

**Material Considerations**:
- UV-resistant filaments (PETG, ASA)
- Corrosion-resistant hardware
- Sealed sensor housing design

**Mechanical Robustness**:
- Adequate thickness for structural integrity
- Flexible mounting to accommodate thermal expansion
- Protection against impact and fouling

---

## Validation and Testing Strategy

### Design Validation
1. **Mathematical Verification**: Confirm Gray code sequences
2. **Geometric Validation**: Check for manufacturing constraints
3. **Simulation Testing**: Verify optical sensor coverage

### Prototype Testing
1. **3D Print Validation**: Test actual printing at specified parameters
2. **Optical Testing**: Verify sensor reading accuracy
3. **Environmental Testing**: Confirm marine environment suitability

### Quality Assurance
1. **Code Review**: Peer review of generation algorithms
2. **Parameter Sweeping**: Test various configurations
3. **Edge Case Testing**: Boundary conditions and error scenarios

---

## Outstanding Issues

### FIXED Issues (October 12, 2025)

**FIXED-001: Track Order Reversal (MSB/LSB)**  
**Status**: RESOLVED  
**Issue**: Tracks were ordered with MSB on outermost track (incorrect)  
**Fix**: Modified `gray_code_bits()` to return `[LSB, ..., MSB]` instead of `[MSB, ..., LSB]`  
**Files Changed**:
- `src/gray_code/converter.py` - Removed `reversed()` in bit extraction
- `src/geometry/track_generator.py` - Updated comments
- `src/gray_code/validator.py` - Updated track descriptions
- `tests/test_gray_code.py` - Updated test expectations
- `docs/ARCHITECTURE.md` - Updated documentation

**FIXED-002: Bit Inversion (Open vs. Closed)**  
**Status**: RESOLVED  
**Issue**: Cutouts created for '0' bits instead of '1' bits (inverted logic)  
**Fix**: Changed cutout generation to create openings for '1' bits (transmissive encoder standard)  
**Files Changed**:
- `src/geometry/track_generator.py` - Changed `if bit_value == 0:` to `if bit_value == 1:`
- Added documentation clarifying transmissive encoder convention

**Result**: Generated disks now match standard Gray code encoder convention with correct track ordering and bit polarity.

---

### High Priority Issues

**TODO-001: Resolve Manufacturing Constraint Inconsistencies**  
**Status**: Critical  
**Location**: `parameters.py` vs `genetic_optimizer.py`  
**Issue**: 
- Default `parameters.py` specifies 0.4mm nozzle diameter constraints
- Genetic optimiser code comments mention 0.16mm line width capability
- Inconsistent min_feature_size, min_gap_size, min_wall_thickness values

**Impact**: May generate designs that fail to print or are over-constrained

**Solution Required**:
```python
# Decision needed: Which constraint set is authoritative?
# Option A: 0.16mm line width (high-precision printer)
min_feature_size_mm = 0.16
min_gap_size_mm = 0.2
min_wall_thickness_mm = 0.32  # 2 perimeters × 0.16mm

# Option B: 0.4mm nozzle (standard printer)
min_feature_size_mm = 0.4
min_gap_size_mm = 0.5
min_wall_thickness_mm = 1.2  # 3 perimeters × 0.4mm
```

**Action Items**:
- Survey target 3D printer capabilities
- Update `parameters.py` with consistent constraints
- Update `genetic_optimizer.py` to use same constraints
- Document chosen constraint set in README
- Add constraint validation

---

**TODO-002: Add Integration Tests**  
**Status**: High Priority  
**Location**: `tests/`  
**Issue**: Unit tests exist but no end-to-end integration tests

**Tests Needed**:
- Full generation pipeline (params → validate → generate → SCAD output)
- Optimisation workflow (optimize → apply → validate → generate)
- GUI critical paths (parameter updates, validation, optimisation)
- Error handling and recovery scenarios
- Multi-configuration generation (default, high_res, compact)

**Example Test Structure**:
```python
def test_full_generation_pipeline():
    """Test complete workflow from parameters to SCAD file"""
    params = create_default_parameters()
    assembler = EncoderAssembler(params)
    disk = assembler.assemble_complete_disk()
    
    # Validate assembly
    valid, errors = assembler.validate_assembly()
    assert valid, f"Assembly failed: {errors}"
    
    # Generate SCAD
    output_file = "test_output.scad"
    scad_render_to_file(disk, output_file)
    assert os.path.exists(output_file)
    assert os.path.getsize(output_file) > 0
```

---

**TODO-003: Unify Validation Pipeline**  
**Status**: Medium-High Priority  
**Location**: Multiple modules  
**Issue**: Validation logic scattered across multiple classes
- `ParameterValidator` in `parameters.py`
- `PrintabilityAnalyzer` in `printer_constraints.py`
- `GrayCodeValidator` in `gray_code/validator.py`
- `EncoderAssembler.validate_assembly()` in `assembly.py`

**Problems**:
- Duplicate validation logic
- Inconsistent error reporting
- No single source of truth
- Difficult to add new validations

**Solution**: Create unified validation pipeline
```python
class EncoderDesignValidator:
    """Unified validation orchestrator"""
    def __init__(self, params: EncoderParameters):
        self.params = params
        self.validators = [
            ParameterValidator(params),
            PrintabilityAnalyzer(),
            GrayCodeValidator(),
        ]
    
    def validate_complete_design(self) -> ValidationReport:
        """Run all validations and aggregate results"""
        report = ValidationReport()
        for validator in self.validators:
            result = validator.validate(self.params)
            report.merge(result)
        return report
```

**Action Items**:
- Design `ValidationReport` data structure
- Create `EncoderDesignValidator` orchestrator class
- Refactor existing validators to common interface
- Update all code to use unified validator
- Add validation result caching

---

### Medium Priority Improvements

**TODO-004: Document Optimisation Results and Sensitivities**  
**Status**: Medium Priority  
**Location**: `docs/`, `output/`  
**Issue**: No documentation of optimisation behaviour and parameter sensitivities

**Needed Documentation**:
- How fitness components affect final design
- Parameter sensitivity analysis (which parameters matter most)
- Convergence behaviour (typical generations needed)
- Trade-offs between optimisation goals
- Example optimisation runs with different starting points
- Guidelines for setting custom optimisation goals

**Deliverables**:
- `docs/OPTIMIZATION_GUIDE.md` with:
  - Fitness function explanation
  - Parameter influence charts
  - Optimisation best practices
  - Troubleshooting guide
- Jupyter notebook with parameter sensitivity analysis

---

**TODO-005: Add Configuration Validation Before Optimisation**  
**Status**: Medium Priority  
**Location**: `genetic_optimizer.py`  
**Issue**: Optimiser doesn't validate fixed parameters before starting

**Problem Scenario**:
```python
# User provides invalid fixed parameters
fixed_params = EncoderParameters(
    outer_diameter_mm=50,    # Too small
    inner_diameter_mm=40,    # Leaves only 10mm for tracks
    num_tracks=10            # Can't fit 10 tracks in 10mm
)
# Optimiser runs 50 generations and finds no valid solution
```

**Solution**:
```python
class EncoderOptimizer:
    def __init__(self, goals, fixed_params=None):
        self.fixed_params = fixed_params
        if fixed_params:
            self._validate_fixed_parameters()
    
    def _validate_fixed_parameters(self):
        """Validate fixed parameters before optimisation starts"""
        validator = ParameterValidator(self.fixed_params)
        valid, errors, warnings = validator.validate_all()
        if not valid:
            raise ValueError(f"Fixed parameters invalid: {errors}")
```

**Action Items**:
- Add pre-optimisation validation
- Provide helpful error messages
- Suggest parameter adjustments
- Add `--dry-run` mode to check feasibility

---

**TODO-006: Improve Error Messages with Actionable Recommendations**  
**Status**: Medium Priority  
**Location**: All validation modules  
**Issue**: Error messages identify problems but don't suggest solutions

**Current Behaviour**:
```
Track spacing 0.3mm less than minimum 0.5mm
```

**Desired Behaviour**:
```
Track spacing 0.3mm less than minimum 0.5mm
Suggestions:
   1. Increase track_spacing_mm to at least 0.5
   2. Reduce number of tracks from 8 to 6
   3. Increase outer_diameter_mm to 150 (provides more space)
```

**Implementation**:
```python
@dataclass
class ValidationError:
    message: str
    severity: str  # 'error', 'warning', 'info'
    affected_params: List[str]
    suggestions: List[str]
    
class SmartValidator:
    def suggest_fixes(self, error: ValidationError) -> List[str]:
        """Generate actionable fix suggestions"""
```

**Action Items**:
- Create `ValidationError` data class
- Implement suggestion engine
- Add fix suggestions to all validators
- Create `--suggest-fixes` CLI option

---

**TODO-007: Add Performance Profiling for Large Designs**  
**Status**: Medium Priority  
**Location**: All generation modules  
**Issue**: No performance metrics for complex designs

**Metrics Needed**:
- Generation time for different position counts (8, 16, 32, 64, 128)
- Memory usage for large track arrays
- SCAD file size vs design complexity
- Optimisation time per generation

**Action Items**:
- Add profiling decorators to hot paths
- Create performance benchmark suite
- Document expected performance characteristics
- Identify optimisation opportunities
- Add progress bars for long operations

---

### Low Priority Enhancements

**TODO-008: Add Architecture Diagrams**  
**Status**: Low Priority  
**Location**: `docs/`  
**Issue**: No visual architecture documentation

**Diagrams Needed**:
- System architecture diagram (module relationships)
- Data flow diagram (parameter → SCAD)
- Optimisation workflow diagram
- Gray code bit extraction illustration
- Track layout visualisation
- Class hierarchy diagrams

Tools: Mermaid, PlantUML, or draw.io

---

**TODO-009: Create Example Configurations Library**  
**Status**: Low Priority  
**Location**: `examples/` or `configs/`  
**Issue**: Only three predefined configs (default, high_res, compact)

**Additional Configs Needed**:
- `micro.json` - Ultra-compact encoder (50mm)
- `marine_heavy_duty.json` - Large, robust design
- `high_precision.json` - Fine resolution (128+ positions)
- `simple_8pos.json` - Beginner-friendly design
- `experimental.json` - Pushing limits

---

**TODO-010: Add Direct STL Export**  
**Status**: Low Priority  
**Location**: `encoder_generator.py`  
**Issue**: Currently outputs only SCAD, requires OpenSCAD for STL conversion

**Desired Feature**:
```bash
python encoder_generator.py --output encoder.stl --format stl
```

**Implementation Options**:
- Use `openscad` command-line tool (subprocess)
- Use Python SCAD libraries with STL export
- Add DXF export for 2D laser cutting

**Action Items**:
- Research STL export options
- Implement `--format` flag
- Add batch export capability
- Support multiple output formats (STL, DXF, STEP)

---

**TODO-011: Implement Parameter Templates System**  
**Status**: Low Priority  
**Location**: `utils/`, GUI  
**Issue**: No way to save/load custom parameter sets

**Desired Features**:
- Save current parameters as named template
- Load template from library
- Share templates between users
- Template versioning and compatibility checking

**GUI Integration**:
- Template dropdown in GUI
- Save/Load buttons
- Template management dialogue

---

**TODO-012: Add Genetic Optimiser Tests**  
**Status**: Low Priority  
**Location**: `tests/`  
**Issue**: No unit tests for genetic optimiser

**Tests Needed**:
- Fitness function correctness
- Mutation respects bounds
- Crossover produces valid genomes
- Tournament selection probabilities
- Convergence detection
- Fixed parameter preservation

---

## Future Enhancements

### Scalability Options
- Parameterised design for different rudder applications
- Multi-resolution encoding (coarse + fine tracks)
- Redundant encoding for safety-critical applications

### Advanced Features
- Built-in calibration patterns
- Temperature compensation marks
- Wear indication features

### Manufacturing Alternatives
- CNC machining option for higher precision
- Laser cutting for metal versions
- Injection moulding for production quantities

---

## References and Standards

### Technical References
- Gray Code: "Reflected Binary Codes" - Frank Gray, Bell System Technical Journal, 1953
- Optical Encoders: "Handbook of Position Location" - S.A. Tretter
- Marine Electronics: NMEA 2000 Standard for instrument interfacing

### Manufacturing Standards
- 3D Printing: ISO/ASTM 52915 for additive manufacturing terminology
- Optical Components: IEC 61203 for fibre optic sensors
- Marine Equipment: ABYC standards for sailboat electrical systems
