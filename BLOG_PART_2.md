# Building A Custom Optical Encoder For Rudder Position Sensing – Part 2

## From Theory to Implementation: The Parametric Design System

In Part 1, I introduced the problem of rudder position sensing for SCANS and explained why Gray code provides reliable absolute position encoding in the presence of mechanical imperfection and electrical noise. This second part examines the implementation: the translation of Gray code theory into manufacturable geometry, the constraints imposed by additive manufacturing, and the application of evolutionary optimization to the parameter space.

The central challenge lies not in the mathematical abstraction of Gray code, but in the practical synthesis of a physical artifact that satisfies multiple competing constraints: manufacturability via fused deposition modeling, reliable optical readability, mechanical robustness, and geometric compatibility with the mounting hardware. The solution required developing a parametric design system that could navigate these constraints systematically.

### Physical Constraints and Design Requirements

The theoretical elegance of Gray code encounters significant practical constraints during physical realization. Fused deposition modeling (FDM) exhibits fundamental limits on minimum feature size determined by nozzle diameter. Optical sensors require minimum feature dimensions for reliable discrimination between transmissive and opaque regions. The encoder disk must possess sufficient structural integrity to resist warping and mechanical stress. Additionally, the design must accommodate specific mounting geometry—in this case, a rudder post of fixed diameter with limited available radial space.

The 256-position, full-rotation encoder described in Part 1 represents one point in a larger design space. A more robust approach required a parametric generator capable of producing valid encoder geometries across a range of specifications: varying position counts, alternative arc angles (for partial-rotation applications), different radial dimensions, and adjustable resolution requirements. Rather than implementing a single fixed design, I developed a system that encodes the mathematical relationships between parameters, validates configurations against manufacturing constraints, and performs automated optimization using genetic algorithms.

### Mathematical Foundation

The system's foundation rests on the Gray code conversion algorithm. For any position $n$ in the range $[0, N-1]$ where $N$ represents the total position count, the Gray code value is computed through the exclusive-OR operation:

$$\text{Gray}(n) = n \oplus (n \gg 1)$$

This bitwise XOR operation between the position value and its right-shifted counterpart produces the single-bit-change property characteristic of Gray code. To generate physical track patterns, individual bits must be extracted from this encoded value.

For an $m$-bit Gray code, where $m = \lceil \log_2(N) \rceil$ represents the minimum number of tracks required, each position encodes as $m$ binary digits. Bit extraction follows:

$$\text{bit}_i = \left(\lfloor\frac{\text{Gray}(n)}{2^i}\rfloor\right) \bmod 2$$

where $i \in [0, m-1]$. This operation corresponds to `(gray_value >> i) & 1` in implementation.

These extracted bits map to concentric physical tracks on the encoder disk. The track assignment follows a specific convention: Track 0 (outermost radius) carries the least significant bit (LSB), while Track $m-1$ (innermost radius) carries the most significant bit (MSB). This radial ordering derives from optical considerations rather than arbitrary choice.

The LSB exhibits the highest transition frequency—approximately every other position—as the encoded sequence increments. Positioning this bit on the outermost track maximizes the arc length of each segment, improving optical sensor reliability. The MSB transitions least frequently (once per half-cycle of the full sequence), making the shorter arc lengths of inner tracks less problematic for detection. This arrangement optimizes the signal-to-noise ratio across all tracks given the geometric constraints of concentric circular tracks.

### Track Layout and Geometric Constraints

Each track occupies an annular sector—a ring segment defined by inner radius, outer radius, and angular extent. For a disk with outer radius $R_{\text{outer}}$ and inner radius $R_{\text{inner}}$ (determined by the mounting hole diameter), tracks are positioned sequentially from the outer edge inward with spacing between adjacent tracks.

Given $m$ tracks with uniform track width $w$ and inter-track spacing $s$, the track pitch $p$ (center-to-center distance) becomes:

$$p = w + s$$

Track $i$, indexed from 0 at the outermost position, occupies radial bounds:

$$R_{\text{outer},i} = R_{\text{outer}} - i \cdot p$$

$$R_{\text{inner},i} = R_{\text{outer},i} - w$$

A fundamental geometric constraint requires that the innermost track not extend below the inner mounting radius:

$$R_{\text{inner},m-1} \geq R_{\text{inner}}$$

This inequality establishes an upper bound on the number of tracks that can be accommodated within the available radial space. The usable radial dimension equals $R_{\text{outer}} - R_{\text{inner}}$, while the radial space required for $m$ tracks totals $m \cdot w + (m-1) \cdot s$. Violation of this constraint renders the design geometrically invalid and triggers validation errors in the parameter checking system.

### From Bit Patterns to Physical Cutouts

The conversion from abstract bit patterns to physical geometry requires determining the spatial distribution of transmissive regions on each track. In a transmissive optical encoder, a '1' bit indicates light transmission through a cutout or slot, while a '0' bit indicates light blockage by solid material.

For each track, the bit pattern across all $N$ positions forms a binary sequence: $[b_0, b_1, b_2, \ldots, b_{N-1}]$ where $b_i \in \{0, 1\}$. Rather than generating individual cutouts for each '1' bit, the algorithm identifies maximal contiguous subsequences of '1' values and creates a single continuous aperture spanning the corresponding angular range. This approach reduces geometric complexity and improves manufacturing reliability.

For positions distributed over arc angle $\theta_{\text{arc}}$, each position corresponds to angular increment:

$$\Delta\theta = \frac{\theta_{\text{arc}}}{N}$$

A contiguous run of $k$ consecutive '1' bits beginning at position $p$ generates a cutout spanning the angular interval $[p \cdot \Delta\theta, (p + k) \cdot \Delta\theta]$. To ensure complete material removal through the disk thickness, the implementation adds a small angular overlap (typically 0.1°) at each boundary and extrudes the cutout to height slightly exceeding the nominal disk thickness.

Geometric primitives are constructed using SolidPython, a Python library providing programmatic generation of OpenSCAD code. Each cutout represents an extruded polygon—specifically, the closed path defining an annular sector. Sector boundary points are computed by parametric generation of arc segments at both inner and outer radii.

For an arc spanning angles $\theta_1$ to $\theta_2$ at radius $R$:

$$x(\theta) = R \cos(\theta)$$

$$y(\theta) = R \sin(\theta)$$

with $\theta$ interpolated over 50 or more discrete steps to achieve smooth curve approximation. The outer arc points are concatenated with reversed inner arc points to form a closed polygon suitable for extrusion.

### Manufacturing Constraints in Fused Deposition Modeling

The transition from theoretical geometry to physical artifact introduces constraints imposed by the additive manufacturing process. Fused deposition modeling operates by extruding thermoplastic through a heated nozzle, with typical diameters of 0.4mm for standard applications or 0.16mm for precision work. This nozzle diameter establishes a lower bound on achievable feature dimensions.

Reliable feature formation requires minimum widths of approximately two nozzle diameters—this provides two perimeter passes that can properly fuse. For a 0.4mm nozzle, features below 0.8mm become unreliable. Inter-feature gaps present similar constraints: insufficient gap width permits unintended bridging where extruded material spans the gap, occluding what should remain transmissive.

The critical parameters affecting manufacturability are gap width (expressed in angular measure) and inter-track spacing. Gap width $\theta_{\text{gap}}$ determines each cutout's angular span. At radius $R$, this angular measure translates to linear dimension:

$$d_{\text{gap}} = \frac{\theta_{\text{gap}} \cdot \pi \cdot R}{180}$$

This gap must exceed minimum thresholds to reliably separate adjacent solid regions. The system incorporates a printability analyzer that evaluates these constraints across all tracks, generating warnings when features approach or violate minimum dimensional thresholds.

A fundamental tension exists between these constraints and design objectives: larger gaps and spacing enable more reliable manufacturing but consume radial space, reducing the number of tracks that fit within available dimensions and thereby limiting resolution. Conversely, aggressive dimensional reduction permits higher track counts and resolution but risks manufacturing failures. This multi-objective optimization problem, involving competing constraints and nonlinear relationships between parameters, motivates the application of evolutionary search algorithms.

### Evolutionary Optimization of the Parameter Space

Rather than manual parameter tuning through iterative trial and error, I implemented a genetic algorithm to perform systematic search of the design space for near-optimal configurations. The algorithm represents each candidate encoder design as a genome—a vector of parameter values completely specifying the disk geometry and encoding characteristics.

The evolutionary process initializes with a population of randomly generated genomes, typically 30 to 50 individuals representing diverse points in the parameter space. Each genome undergoes evaluation via a multi-objective fitness function scoring performance across several criteria:

Printability (weighted at 40% of total fitness) assesses manufacturability by evaluating minimum feature sizes, gap widths, track spacing, and wall thicknesses against FDM constraints. Designs violating printability requirements receive substantial fitness penalties, effectively steering the population toward manufacturable solutions.

Resolution (20% weight) quantifies the encoder's ability to distinguish discrete positions. Higher position counts generally improve angular resolution, though with diminishing returns beyond certain thresholds and subject to physical size constraints.

Encoding efficiency (20% weight) measures Gray code utilization relative to track count. For $m$ tracks supporting up to $2^m$ distinct codes, using exactly a power-of-two position count (e.g., 32 positions with 5 tracks) achieves 100% efficiency. Configurations using fewer than $2^m$ positions exhibit lower efficiency due to unused code space.

Size optimization (10% weight) rewards designs approaching the target outer diameter. Significant deviation either direction indicates suboptimal space utilization or geometric incompatibility with mounting constraints.

Manufacturability (10% weight) captures secondary considerations including preference for standard dimensional values, reasonable arc angles, and design simplicity affecting assembly and optical alignment.

The fitness function computes a weighted sum of these normalized component scores, with a 20% multiplicative bonus applied to genomes satisfying all validation constraints. Invalid parameter combinations receive zero fitness, eliminating them from reproduction.

Evolution proceeds through tournament selection, where small randomly-chosen subsets compete and the highest-fitness individual from each tournament becomes a parent for the next generation. Elitism preserves the top 10% of each generation unchanged, preventing loss of high-quality solutions. Remaining positions in the next generation are filled by offspring generated through crossover and mutation operations.

Crossover combines parental genomes by randomly inheriting each optimizable parameter (track width, track spacing, gap width) from one parent or the other. Mutation subsequently introduces variation through bounded random perturbations, typically ±20% of current values, with parameter-specific range constraints preventing physically impossible values.

A critical feature permits fixing certain parameters while optimizing others. For the rudder encoder application, mounting geometry dictates outer diameter, inner diameter, and arc angle as fixed constraints determined by mechanical requirements. The algorithm holds these constant while optimizing the track layout parameters governing optical performance and manufacturability. This constrained optimization focuses computational effort on the actual degrees of freedom in the design problem.

The algorithm executes for a complete generation count—typically 50 generations—without implementing early termination criteria. This ensures thorough exploration of the parameter space rather than premature convergence to local optima. Empirical observation indicates that novel high-quality solutions often emerge in later generations as the population converges toward optimal regions of the search space.

Application of this genetic algorithm to my rudder encoder specifications yielded a best-fitness solution of 1.115 after 50 generations. The optimized parameter set comprises 32 positions (5-bit Gray code), 116.2mm outer diameter, 35.6mm inner diameter, 57.1° arc angle, 3.3mm track width, 1.7mm track spacing, and 2.8° gap width. These values replaced the initial hand-tuned parameters as the system's default configuration.

### Software Architecture

The encoder generator implements a modular architecture with clear separation of concerns across functional domains. The Gray code mathematics resides in an independent module providing functions for position-to-Gray-code conversion, bit pattern extraction, sequence validation, and track characteristic analysis. This module operates without dependencies on geometry generation or manufacturing constraints, facilitating independent testing and reuse.

The geometry module consumes bit patterns from the Gray code subsystem and generates three-dimensional solid representations using the SolidPython library. It implements primitives for arc sector creation, manages track layout calculations, and performs Boolean operations (union, difference) combining base disk geometry with cutout patterns.

Parameter validation operates through multiple specialized subsystems. Basic geometric validation verifies that outer radius exceeds inner radius, arc angles fall within acceptable bounds, and track counts match required bit depths. Encoding validation confirms Gray code pattern correctness. Printability analysis evaluates feature dimensions against manufacturing constraints. This multi-layer validation architecture detects constraint violations early in the design process, providing detailed diagnostic messages and suggested parameter adjustments.

The genetic optimizer integrates these subsystems, utilizing validation for fitness evaluation and geometry generation for design verification. The optimizer maintains clean separation between genome representation, fitness evaluation logic, and evolutionary operators (selection, crossover, mutation), facilitating independent modification of each component.

Three user interfaces provide access to the generation system: a command-line interface supporting scripting and automated workflows, a PyQt6 graphical interface enabling interactive parameter exploration, and a Makefile-based build system for common operations. All interfaces utilize the same underlying generation engine, ensuring consistency across access methods.

### Generation Pipeline

Encoder disk generation proceeds through a well-defined pipeline with explicit validation at each stage. The process begins with parameter specification, either from predefined configurations (default, high-resolution, compact) or custom values loaded from configuration files. The validation subsystem evaluates these parameters against all constraint categories, reporting errors or warnings that indicate potential design issues.

Upon successful validation, the Gray code pattern generator produces bit sequences for all tracks. For each position $p \in [0, N-1]$, the system computes Gray code value and extracts the $m$ constituent bits. These bits assemble into track patterns—binary sequences indicating which positions require transmissive apertures on each track.

The track generator then transforms binary patterns into three-dimensional geometric primitives. The algorithm identifies maximal contiguous subsequences of '1' bits and generates corresponding arc sector cutouts at appropriate radii and angular positions. All cutouts across all tracks combine via union operation to form a single composite cutout geometry, improving computational efficiency.

Base disk construction creates an annular sector spanning inner to outer radius over the specified arc angle. Optional limit switch bumpers—rectangular protrusions at the 0° and terminal positions—provide mechanical triggers for detecting extreme rudder positions. These bumpers serve as failsafe indicators independent of the optical encoding system.

Final disk assembly employs Boolean difference: the union of solid components (base disk and optional bumpers) minus the union of all cutout patterns. This operation yields a single coherent three-dimensional solid representing the complete encoder disk geometry.

The SolidPython library renders this geometric representation to OpenSCAD source code—a text-based declarative description of the geometry suitable for visualization and STL export. The generated file includes header comments documenting all design parameters and recommended fabrication settings (layer height, perimeter count, infill percentage, print speed, material selection) derived from the printability analysis.

### Observations on Implementation

The development of this system revealed that the distance between mathematical abstraction and physical realization represents the domain where engineering problems become substantive. While Gray code's theoretical properties are well-established, achieving reliable performance in physical systems requires addressing additive manufacturing limitations, optical sensor characteristics, mechanical tolerances, and the complex interactions between geometric parameters.

The genetic algorithm initially served as a computational convenience—a method to avoid manual parameter optimization. During development, it demonstrated broader utility: the algorithm explores parameter combinations that would not emerge from intuitive reasoning or conventional design heuristics. Unconstrained by preconceptions about viable configurations, the evolutionary search identifies solutions that satisfy multiple competing objectives in non-obvious ways. The fitness function and constraint definitions encode engineering knowledge about what constitutes a valid design, while the search algorithm discovers how to achieve those goals within the defined parameter space.

The most significant outcome extends beyond the specific rudder encoder: the parametric design system provides adaptability to varying requirements. Modifications to mounting constraints, resolution specifications, or manufacturing capabilities require parameter adjustments rather than fundamental redesign. The same codebase that generated the rudder encoder can produce encoders for alternative applications with different position counts, arc angles, or dimensional constraints.

### Future Work

Part 3 will examine the sensor electronics and firmware implementation: the optical sensing circuit design incorporating infrared LED/phototransistor pairs, signal conditioning and digitization, ROS-2 interface development, noise mitigation strategies, calibration procedures, and integration with the SCANS autopilot architecture. Additionally, I will discuss the mechanical mounting solution, fabrication methods, and empirical validation through testing of the first prototype.

The design demonstrates that sophisticated computational tools augment rather than replace engineering judgment. The genetic algorithm does not autonomously design the encoder—it explores the design space I have defined through parameter selection, constraint formulation, and fitness function specification. The quality of the optimization result depends critically on how accurately these elements capture the characteristics of effective encoder designs.

The implementation code is available via GitHub, and the current optimized design has been prepared for fabrication. The subsequent phase involves empirical validation: determining whether this theoretical encoder performs reliably under operational conditions.

---

*Published November 8, 2025*

