"""
Genetic Algorithm Optimizer for Rudder Encoder Parameters

This module uses evolutionary algorithms to find optimal encoder parameters
that satisfy manufacturing constraints while maximizing functionality.
"""

import random
import math
import statistics
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import json
import sys
import os

# Add src to path
current_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(current_dir))

from utils import EncoderParameters, ParameterValidator, PrintabilityAnalyzer
from gray_code import GrayCodeValidator


@dataclass
class OptimizationGoals:
    """Defines the optimization goals and constraints."""

    # Primary goals
    min_positions: int = 16  # Minimum resolution required
    max_positions: int = 64  # Maximum practical resolution
    target_outer_diameter: float = 100.0  # Preferred size
    target_arc_angle: float = 30.0  # Rudder travel range

    # Constraints
    max_outer_diameter: float = 150.0  # Build volume limit
    min_feature_size: float = 0.5  # 3D printing minimum
    max_tracks: int = 8  # Sensor array limit

    # Weights for fitness function
    weight_printability: float = 0.4  # Most important
    weight_resolution: float = 0.2  # Position accuracy
    weight_efficiency: float = 0.2  # Gray code utilization
    weight_size: float = 0.1  # Compactness
    weight_manufacturability: float = 0.1  # Ease of production


class ParameterGenome:
    """Represents a parameter set as a genome for genetic algorithm."""

    def __init__(
        self,
        params: Optional[EncoderParameters] = None,
        fixed_params: Optional[EncoderParameters] = None,
    ):
        if params:
            self.params = params
        else:
            self.params = self._random_parameters(fixed_params)

        self.fitness: float = 0.0
        self.validated: bool = False
        self.fitness_components: Dict[str, float] = {}

    def _random_parameters(
        self, fixed_params: Optional[EncoderParameters] = None
    ) -> EncoderParameters:
        """
        Generate random parameters within reasonable bounds, keeping fixed
        parameters unchanged.
        """
        if fixed_params:
            # Start with fixed parameters
            params = EncoderParameters(
                # Fixed physical dimensions (from user requirements)
                outer_diameter_mm=fixed_params.outer_diameter_mm,
                inner_diameter_mm=fixed_params.inner_diameter_mm,
                disk_thickness_mm=fixed_params.disk_thickness_mm,
                arc_angle_deg=fixed_params.arc_angle_deg,
                num_positions=fixed_params.num_positions,
                num_tracks=fixed_params.num_tracks,
                bump_extension_mm=fixed_params.bump_extension_mm,
                bump_width_deg=fixed_params.bump_width_deg,
                # Only randomize track layout parameters
                track_width_mm=random.uniform(0.5, 5.0),  # Optimizable
                track_spacing_mm=random.uniform(0.2, 2.0),  # Optimizable
                gap_width_deg=random.uniform(0.5, 4.0),  # Optimizable
                # Manufacturing constraints for 0.16mm line width
                min_feature_size_mm=0.16,
                min_gap_size_mm=0.2,
                min_wall_thickness_mm=0.32,  # 2 perimeters at 0.16mm
            )
        else:
            # Fallback to old behavior if no fixed params provided
            position_options = [8, 16, 32, 64]
            num_positions = random.choice(position_options)
            num_tracks = int(math.ceil(math.log2(num_positions)))

            params = EncoderParameters()
            params.outer_diameter_mm = random.uniform(80, 150)
            params.inner_diameter_mm = random.uniform(20, 40)
            params.disk_thickness_mm = random.uniform(2, 5)
            params.arc_angle_deg = random.uniform(20, 60)
            params.num_positions = num_positions
            params.num_tracks = num_tracks
            params.track_width_mm = random.uniform(3, 8)
            params.track_spacing_mm = random.uniform(1, 3)
            params.gap_width_deg = random.uniform(1, 4)
            params.bump_extension_mm = random.uniform(3, 8)
            params.bump_width_deg = random.uniform(1, 3)

        return params

    def mutate(
        self,
        mutation_rate: float = 0.1,
        fixed_params: Optional[EncoderParameters] = None,
    ):
        """
        Apply random mutations to parameters, only changing optimizable
        track layout parameters.
        """
        if random.random() < mutation_rate:
            # Only mutate track layout parameters - keep physical/encoding params fixed
            optimizable_params = ["track_width_mm", "track_spacing_mm", "gap_width_deg"]

            param_name = random.choice(optimizable_params)
            current_value = getattr(self.params, param_name)

            # Apply small random change (±20%)
            change_factor = random.uniform(0.8, 1.2)
            new_value = current_value * change_factor

            # Apply bounds based on 0.16mm manufacturing capability
            if param_name == "track_width_mm":
                new_value = max(
                    0.32, min(8.0, new_value)
                )  # Min 2 line widths, reasonable max
            elif param_name == "track_spacing_mm":
                new_value = max(
                    0.2, min(3.0, new_value)
                )  # Min gap size, reasonable max
            elif param_name == "gap_width_deg":
                new_value = max(0.3, min(6.0, new_value))  # Small gaps to large gaps

            setattr(self.params, param_name, new_value)

        self.validated = False  # Need to re-validate after mutation

        # Reset fitness after mutation
        self.fitness = 0.0
        self.validated = False

    def crossover(
        self, other: "ParameterGenome"
    ) -> Tuple["ParameterGenome", "ParameterGenome"]:
        """
        Create offspring through crossover, only crossing over optimizable
        parameters.
        """
        child1_params = EncoderParameters()
        child2_params = EncoderParameters()

        # Copy all data attributes from self to both children
        # (preserving fixed parameters)
        data_attrs = [
            "outer_diameter_mm",
            "inner_diameter_mm",
            "disk_thickness_mm",
            "arc_angle_deg",
            "num_positions",
            "num_tracks",
            "track_width_mm",
            "track_spacing_mm",
            "gap_width_deg",
            "bump_extension_mm",
            "bump_width_deg",
            "min_feature_size_mm",
            "min_gap_size_mm",
            "min_wall_thickness_mm",
        ]

        for attr_name in data_attrs:
            if hasattr(self.params, attr_name):
                setattr(child1_params, attr_name, getattr(self.params, attr_name))
                setattr(child2_params, attr_name, getattr(self.params, attr_name))

        # Only crossover the optimizable track layout parameters
        optimizable_params = [
            "track_width_mm",
            "track_spacing_mm",
            "gap_width_deg",
        ]

        # Uniform crossover for optimizable parameters only
        for param_name in optimizable_params:
            if random.random() < 0.5:
                setattr(child1_params, param_name, getattr(self.params, param_name))
                setattr(child2_params, param_name, getattr(other.params, param_name))
            else:
                setattr(child1_params, param_name, getattr(other.params, param_name))
                setattr(child2_params, param_name, getattr(self.params, param_name))

        return ParameterGenome(child1_params), ParameterGenome(child2_params)


class EncoderOptimizer:
    """Genetic algorithm optimizer for encoder parameters."""

    def __init__(
        self, goals: OptimizationGoals, fixed_params: Optional[EncoderParameters] = None
    ):
        self.goals = goals
        self.fixed_params = fixed_params
        self.population: List[ParameterGenome] = []
        self.generation = 0
        self.best_genome: Optional[ParameterGenome] = None
        self.fitness_history: List[float] = []
        self.convergence_threshold = 0.001
        self.stagnation_limit = 20

    def initialize_population(self, size: int = 50):
        """Initialize random population."""
        print(f" Initializing population of {size} genomes...")
        if self.fixed_params:
            print(
                f" Using fixed parameters: "
                f"{self.fixed_params.outer_diameter_mm:.1f}mm ⌀, "
                f"{self.fixed_params.inner_diameter_mm:.1f}mm inner, "
                f"{self.fixed_params.arc_angle_deg:.1f}° arc"
            )
            print(
                f" Optimizing only track layout parameters "
                f"(width, spacing, gap)"
            )
            self.population = [
                ParameterGenome(fixed_params=self.fixed_params) for _ in range(size)
            ]
        else:
            self.population = [ParameterGenome() for _ in range(size)]

    def evaluate_fitness(self, genome: ParameterGenome) -> float:
        """Evaluate fitness of a genome based on multiple criteria."""
        if genome.validated:
            return genome.fitness

        params = genome.params
        fitness_components = {}

        # 1. Parameter validation (basic constraints)
        validator = ParameterValidator(params)
        param_valid, param_errors, param_warnings = validator.validate_all()

        if not param_valid:
            genome.fitness = 0.0  # Invalid genomes get zero fitness
            genome.validated = True
            return 0.0

        # 2. Printability assessment
        print_analyzer = PrintabilityAnalyzer()
        (
            print_valid,
            print_issues,
            print_recommendations,
        ) = print_analyzer.analyze_encoder_design(params)

        printability_score = (
            1.0 if print_valid else max(0.1, 1.0 - len(print_issues) * 0.2)
        )
        fitness_components["printability"] = printability_score

        # 3. Gray code validation
        gray_validator = GrayCodeValidator()
        gray_valid, gray_report = gray_validator.validate_encoder_pattern(
            params.num_positions, params.num_tracks
        )

        gray_score = (
            1.0 if gray_valid else max(0.2, 1.0 - len(gray_report["errors"]) * 0.3)
        )
        if gray_report["warnings"]:
            gray_score *= max(0.5, 1.0 - len(gray_report["warnings"]) * 0.1)

        # 4. Resolution score (how close to target positions)
        resolution_score = 1.0
        if params.num_positions < self.goals.min_positions:
            resolution_score *= 0.3  # Heavily penalize insufficient resolution
        elif params.num_positions > self.goals.max_positions:
            resolution_score *= 0.7  # Penalize excessive resolution
        else:
            # Bonus for being in the sweet spot
            target_mid = (self.goals.min_positions + self.goals.max_positions) / 2
            distance_from_target = abs(params.num_positions - target_mid) / target_mid
            resolution_score = max(0.7, 1.0 - distance_from_target)

        fitness_components["resolution"] = resolution_score

        # 5. Encoding efficiency
        efficiency = params.num_positions / (2**params.num_tracks)
        efficiency_score = efficiency  # Direct mapping
        fitness_components["efficiency"] = efficiency_score

        # 6. Size optimization (prefer target diameter)
        size_diff = abs(params.outer_diameter_mm - self.goals.target_outer_diameter)
        size_score = max(0.3, 1.0 - size_diff / self.goals.target_outer_diameter)
        fitness_components["size"] = size_score

        # 7. Manufacturability (simpler is better)
        manufacturability_score = 1.0

        # Prefer fewer tracks
        if params.num_tracks > 6:
            manufacturability_score *= 0.8

        # Prefer reasonable arc angles
        arc_diff = abs(params.arc_angle_deg - self.goals.target_arc_angle)
        if arc_diff > 15:
            manufacturability_score *= 0.9

        # Prefer standard track dimensions
        if params.track_width_mm < 4 or params.track_width_mm > 7:
            manufacturability_score *= 0.95

        fitness_components["manufacturability"] = manufacturability_score

        # Calculate weighted fitness
        total_fitness = (
            self.goals.weight_printability * printability_score
            + self.goals.weight_resolution * resolution_score
            + self.goals.weight_efficiency * efficiency_score
            + self.goals.weight_size * size_score
            + self.goals.weight_manufacturability * manufacturability_score
        )

        # Bonus for being fully valid
        if param_valid and print_valid and gray_valid:
            total_fitness *= 1.2

        genome.fitness = total_fitness
        genome.fitness_components = fitness_components
        genome.validated = True

        return total_fitness

    def select_parents(self, tournament_size: int = 5) -> List[ParameterGenome]:
        """Tournament selection for parent genomes."""
        selected = []

        for _ in range(len(self.population)):
            tournament = random.sample(self.population, tournament_size)
            winner = max(tournament, key=lambda g: g.fitness)
            selected.append(winner)

        return selected

    def evolve_generation(self):
        """Evolve one generation."""
        # Evaluate fitness for all genomes
        for genome in self.population:
            self.evaluate_fitness(genome)

        # Sort by fitness
        self.population.sort(key=lambda g: g.fitness, reverse=True)

        # Track best genome
        if (
            not self.best_genome
            or self.population[0].fitness > self.best_genome.fitness
        ):
            self.best_genome = ParameterGenome(self.population[0].params)
            self.best_genome.fitness = self.population[0].fitness
            self.best_genome.fitness_components = (
                self.population[0].fitness_components.copy()
            )

        # Record fitness statistics
        fitnesses = [g.fitness for g in self.population]
        avg_fitness = statistics.mean(fitnesses)
        self.fitness_history.append(avg_fitness)

        print(
            f"Generation {self.generation}: "
            f"Best={self.population[0].fitness:.3f}, "
            f"Avg={avg_fitness:.3f}, "
            f"Valid={sum(1 for g in self.population if g.fitness > 0)}"
        )

        # Create next generation
        elite_size = max(2, len(self.population) // 10)  # Keep top 10%
        new_population = self.population[:elite_size]  # Elitism

        # Fill rest with offspring
        parents = self.select_parents()
        while len(new_population) < len(self.population):
            parent1, parent2 = random.sample(parents, 2)
            child1, child2 = parent1.crossover(parent2)

            child1.mutate(fixed_params=self.fixed_params)
            child2.mutate(fixed_params=self.fixed_params)

            new_population.extend([child1, child2])

        # Trim to exact size
        self.population = new_population[: len(self.population)]
        self.generation += 1

    def optimize(
        self, generations: int = 100, population_size: int = 50
    ) -> ParameterGenome:
        """Run the genetic algorithm optimization."""
        print(" Starting genetic algorithm optimization...")
        print(
            f"Target: {self.goals.min_positions}-{self.goals.max_positions} positions, "
            f"{self.goals.target_outer_diameter}mm diameter"
        )
        print(f"Configuration: {generations} generations, {population_size} population")

        self.initialize_population(population_size)

        stagnation_counter = 0
        last_best_fitness = 0.0

        print(f"\n Starting evolution loop...")

        for gen in range(generations):
            print(f"\n--- Generation {gen + 1}/{generations} ---")
            self.evolve_generation()

            # Check for convergence
            if self.best_genome:
                fitness_improvement = (
                    self.best_genome.fitness - last_best_fitness
                )
                print(f" Fitness improvement: {fitness_improvement:.6f}")

                if fitness_improvement < self.convergence_threshold:
                    stagnation_counter += 1
                    print(
                        f"  Stagnation counter: "
                        f"{stagnation_counter}/{self.stagnation_limit} "
                        f"(continuing to explore)"
                    )
                else:
                    stagnation_counter = 0
                    last_best_fitness = self.best_genome.fitness
                    print(f" New best fitness: {last_best_fitness:.3f}")

                # Note: Removed early stopping to fully explore solution space
                # Algorithm will run all generations to find the absolute
                # best solution

                # Log progress but continue exploring solution space
                if self.best_genome.fitness > 1.2:
                    print(
                        f" Excellent solution found "
                        f"(fitness: {self.best_genome.fitness:.3f}), "
                        f"continuing to explore solution space..."
                    )
                elif self.best_genome.fitness > 1.0:
                    print(
                        f" Good solution found "
                        f"(fitness: {self.best_genome.fitness:.3f}), "
                        f"searching for better..."
                    )

                # Continue evolution to fully explore solution space
                # No early stopping!
            else:
                print("  No valid genome found yet")

        print(f"\n Solution Space Exploration Complete!")
        print(
            f" Ran all {self.generation} generations "
            f"to find optimal solution"
        )
        if self.best_genome:
            print(f" Best fitness achieved: {self.best_genome.fitness:.3f}")
            print(
                f" Fitness evolution: "
                f"{self.fitness_history[0]:.3f} → "
                f"{self.best_genome.fitness:.3f}"
            )
            self._print_best_solution()
        else:
            print(" No valid solution found")

        return self.best_genome

    def _print_best_solution(self):
        """Print details of the best solution found."""
        if not self.best_genome:
            print("No valid solution found")
            return

        params = self.best_genome.params
        components = self.best_genome.fitness_components

        print("\n Best Solution:")
        print(f"   Positions: {params.num_positions} ({params.num_tracks} tracks)")
        print(
            f"   Dimensions: {params.outer_diameter_mm:.1f}mm ⌀, "
            f"{params.arc_angle_deg:.1f}°"
        )
        print(
            f"   Tracks: {params.track_width_mm:.1f}mm wide, "
            f"{params.track_spacing_mm:.1f}mm spacing"
        )
        print(f"   Gap width: {params.gap_width_deg:.1f}°")
        print(
            f"   Encoding efficiency: "
            f"{params.num_positions / (2**params.num_tracks)*100:.1f}%"
        )

        print("\n Fitness Breakdown:")
        for component, score in components.items():
            print(f"   {component.capitalize()}: {score:.3f}")

    def export_best_solution(self, filename: str):
        """Export the best solution to a file."""
        if not self.best_genome:
            print("No solution to export")
            return

        export_data = {
            "optimization_results": {
                "generations": self.generation,
                "best_fitness": self.best_genome.fitness,
                "fitness_components": self.best_genome.fitness_components,
            },
            "parameters": asdict(self.best_genome.params),
            "goals": asdict(self.goals),
        }

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"💾 Best solution exported to {filename}")


def main():
    """Main optimization routine."""
    print(" Genetic Algorithm Encoder Optimization")
    print("=" * 50)

    # Define your fixed parameters (user requirements)
    fixed_params = EncoderParameters(
        # Fixed physical dimensions - DO NOT OPTIMIZE
        outer_diameter_mm=100.0,  # Your encoder width requirement
        inner_diameter_mm=35.0,  # Your rudder post requirement (35mm radius)
        arc_angle_deg=90.0,  # Updated default to 90° arc sweep
        disk_thickness_mm=3.0,  # Reasonable thickness
        # Fixed encoding parameters - DO NOT OPTIMIZE
        num_positions=32,  # Good resolution for rudder position
        num_tracks=5,  # Required for 32 positions (2^5 = 32)
        # Fixed bumpers - DO NOT OPTIMIZE
        bump_extension_mm=5.0,
        bump_width_deg=2.0,
        # Manufacturing constraints for 0.16mm line width
        min_feature_size_mm=0.16,
        min_gap_size_mm=0.2,
        min_wall_thickness_mm=0.32,
        # Initial track layout values - THESE WILL BE OPTIMIZED
        track_width_mm=2.0,  # Starting value, will be optimized
        track_spacing_mm=1.0,  # Starting value, will be optimized
        gap_width_deg=2.0,  # Starting value, will be optimized
    )

    # Define optimization goals
    goals = OptimizationGoals()

    # Allow command line customization of goals only
    if len(sys.argv) > 1:
        if "high_res" in sys.argv:
            goals.min_tracks = 8
            goals.min_resolution = 1.5
            print(" High resolution optimization mode")
        elif "compact" in sys.argv:
            goals.max_noise_ratio = 0.15
            goals.target_strength = 0.7
            print(" Compact optimization mode")

    print(f" Fixed Parameters:")
    print(f"   Outer diameter: {fixed_params.outer_diameter_mm}mm")
    print(f"   Inner diameter: {fixed_params.inner_diameter_mm}mm")
    print(f"   Arc angle: {fixed_params.arc_angle_deg}°")
    print(f"   Positions: {fixed_params.num_positions}")
    print(f"   Manufacturing: {fixed_params.min_feature_size_mm}mm line width")

    # Run optimization with fixed parameters
    optimizer = EncoderOptimizer(goals, fixed_params)
    best_solution = optimizer.optimize(generations=50, population_size=30)

    if best_solution:
        # Export results
        output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
        os.makedirs(output_dir, exist_ok=True)

        results_file = os.path.join(output_dir, "optimized_parameters.json")
        optimizer.export_best_solution(results_file)

        # Generate the optimized encoder
        try:
            from encoder_generator import generate_encoder

            output_file = os.path.join(output_dir, "optimized_encoder.scad")
            success = generate_encoder(best_solution.params, output_file, verbose=True)
            if success:
                print(f"🎉 Optimized encoder generated: {output_file}")
        except Exception as e:
            print(f"  Could not generate encoder: {e}")

    else:
        print(" No valid solution found. Try adjusting optimization goals.")


if __name__ == "__main__":
    main()
