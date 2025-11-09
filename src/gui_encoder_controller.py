"""
Rudder Encoder Disk Generator - GUI Controller

A PyQt6-based graphical interface for controlling encoder disk parameters,
running genetic optimization, and generating 3D printable encoder disks.
"""

import sys
import os
import json
import threading
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QTabWidget,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QProgressBar,
    QMessageBox,
    QFileDialog,
    QCheckBox,
    QComboBox,
    QSplitter,
    QFrame,
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor


class OptimizationWorker(QThread):
    """Worker thread for running genetic optimization without blocking the UI."""

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(
        self, parameters: Dict[str, Any], generations: int = 100, population: int = 30
    ):
        super().__init__()
        self.parameters = parameters
        self.generations = generations
        self.population = population

    def run(self):
        """Run the genetic optimization in a separate thread."""
        try:
            self.progress.emit(" Starting genetic optimization...")

            # Import here to avoid import issues in main thread
            sys.path.append(os.path.join(os.path.dirname(__file__)))
            from genetic_optimizer import EncoderOptimizer, OptimizationGoals
            from utils.parameters import EncoderParameters
            import dataclasses

            # Create parameters object from GUI values (these will be fixed)
            gui_params = EncoderParameters(**self.parameters)

            # Create optimization goals based on current parameters
            goals = OptimizationGoals()
            goals.min_positions = max(8, gui_params.num_positions // 2)
            goals.max_positions = min(256, gui_params.num_positions * 2)
            goals.target_outer_diameter = gui_params.outer_diameter_mm
            goals.target_arc_angle = gui_params.arc_angle_deg

            self.progress.emit(
                f" Target: {goals.min_positions}-{goals.max_positions} positions"
            )
            self.progress.emit(
                f" Target diameter: {goals.target_outer_diameter:.1f}mm"
            )
            self.progress.emit(
                f" Fixed GUI parameters: "
                f"{gui_params.outer_diameter_mm:.1f}mm ⌀, "
                f"{gui_params.inner_diameter_mm:.1f}mm inner, "
                f"{gui_params.arc_angle_deg:.1f}° arc"
            )
            self.progress.emit(
                f" Optimizing only track layout "
                f"(width: {gui_params.track_width_mm:.1f}mm, "
                f"spacing: {gui_params.track_spacing_mm:.1f}mm, "
                f"gap: {gui_params.gap_width_deg:.1f}°)"
            )

            # Create and run optimizer with fixed GUI parameters
            optimizer = EncoderOptimizer(goals, fixed_params=gui_params)

            self.progress.emit(
                f" Running {self.generations} generations "
                f"with population {self.population}..."
            )

            # Run optimization
            best_genome = optimizer.optimize(
                generations=self.generations, population_size=self.population
            )

            if not best_genome:
                raise ValueError("No valid solution found")

            # Convert result to dictionary
            result = {
                "parameters": dataclasses.asdict(best_genome.params),
                "fitness": best_genome.fitness,
                "generation": optimizer.generation,
                "fitness_components": best_genome.fitness_components,
            }

            self.progress.emit(
                f" Optimization complete! Best fitness: {best_genome.fitness:.3f}"
            )
            self.finished.emit(result)

        except Exception as e:
            self.error.emit(f" Optimization failed: {str(e)}")


class ValidationWorker(QThread):
    """Worker thread for validating parameters."""

    finished = pyqtSignal(bool, list, list)
    error = pyqtSignal(str)

    def __init__(self, parameters: Dict[str, Any]):
        super().__init__()
        self.parameters = parameters

    def run(self):
        """Validate parameters in a separate thread."""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__)))
            from utils.parameters import EncoderParameters, ParameterValidator

            # Create parameters object
            params = EncoderParameters(**self.parameters)

            # Validate
            validator = ParameterValidator(params)
            is_valid, errors, warnings = validator.validate_all()

            self.finished.emit(is_valid, errors, warnings)

        except Exception as e:
            self.error.emit(f" Validation failed: {str(e)}")


class EncoderControllerGUI(QMainWindow):
    """Main GUI window for the Encoder Disk Controller."""

    def __init__(self):
        super().__init__()
        self.current_parameters = {}
        self.optimization_results = {}
        self.project_root = Path(__file__).parent.parent

        self.init_ui()
        self.load_default_parameters()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("🚢 Rudder Encoder Disk Generator")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Parameters and controls
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel - Output and results
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([400, 800])

        # Status bar
        self.statusBar().showMessage("Ready")

        # Style the application
        self.apply_styling()

    def create_left_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Title
        title = QLabel(" Encoder Parameters")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Physical dimensions group
        layout.addWidget(self.create_physical_group())

        # Encoding parameters group
        layout.addWidget(self.create_encoding_group())

        # Track layout group
        layout.addWidget(self.create_track_group())

        # Control buttons
        layout.addWidget(self.create_control_buttons())

        # Stretch to push everything to top
        layout.addStretch()

        return panel

    def create_physical_group(self) -> QGroupBox:
        """Create physical dimensions parameter group."""
        group = QGroupBox(" Physical Dimensions")
        layout = QGridLayout(group)

        # Inner radius (rudder post)
        layout.addWidget(QLabel("Inner Radius (mm):"), 0, 0)
        self.inner_radius_spin = QDoubleSpinBox()
        self.inner_radius_spin.setRange(10.0, 100.0)
        self.inner_radius_spin.setValue(35.0)  # User's requirement
        self.inner_radius_spin.setDecimals(1)
        self.inner_radius_spin.setSuffix(" mm")
        layout.addWidget(self.inner_radius_spin, 0, 1)

        # Encoder width
        layout.addWidget(QLabel("Encoder Width (mm):"), 1, 0)
        self.encoder_width_spin = QDoubleSpinBox()
        self.encoder_width_spin.setRange(20.0, 200.0)
        self.encoder_width_spin.setValue(100.0)  # User's requirement
        self.encoder_width_spin.setDecimals(1)
        self.encoder_width_spin.setSuffix(" mm")
        layout.addWidget(self.encoder_width_spin, 1, 1)

        # Arc angle
        layout.addWidget(QLabel("Arc Angle (degrees):"), 2, 0)
        self.arc_angle_spin = QDoubleSpinBox()
        self.arc_angle_spin.setRange(5.0, 360.0)
        self.arc_angle_spin.setValue(90.0)  # Updated default to 90 degrees
        self.arc_angle_spin.setDecimals(1)
        self.arc_angle_spin.setSuffix("°")
        layout.addWidget(self.arc_angle_spin, 2, 1)

        # Disk thickness
        layout.addWidget(QLabel("Disk Thickness (mm):"), 3, 0)
        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(1.0, 10.0)
        self.thickness_spin.setValue(2.5)
        self.thickness_spin.setDecimals(1)
        self.thickness_spin.setSuffix(" mm")
        layout.addWidget(self.thickness_spin, 3, 1)

        # Auto-calculate outer diameter
        layout.addWidget(QLabel("Outer Diameter:"), 4, 0)
        self.outer_diameter_label = QLabel("170.0 mm")
        self.outer_diameter_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        layout.addWidget(self.outer_diameter_label, 4, 1)

        # Connect signals for auto-calculation
        self.inner_radius_spin.valueChanged.connect(self.update_calculated_values)
        self.encoder_width_spin.valueChanged.connect(self.update_calculated_values)

        return group

    def create_encoding_group(self) -> QGroupBox:
        """Create encoding parameters group."""
        group = QGroupBox("🔢 Encoding Parameters")
        layout = QGridLayout(group)

        # Number of positions
        layout.addWidget(QLabel("Positions:"), 0, 0)
        self.positions_combo = QComboBox()
        self.positions_combo.addItems(["8", "16", "32", "64", "128", "256"])
        self.positions_combo.setCurrentText("32")
        layout.addWidget(self.positions_combo, 0, 1)

        # Auto-calculate tracks
        layout.addWidget(QLabel("Tracks (bits):"), 1, 0)
        self.tracks_label = QLabel("5")
        self.tracks_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        layout.addWidget(self.tracks_label, 1, 1)

        # Angular resolution
        layout.addWidget(QLabel("Resolution:"), 2, 0)
        self.resolution_label = QLabel("0.78°")
        self.resolution_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        layout.addWidget(self.resolution_label, 2, 1)

        # Connect signal
        self.positions_combo.currentTextChanged.connect(self.update_calculated_values)

        return group

    def create_track_group(self) -> QGroupBox:
        """Create track layout parameters group."""
        group = QGroupBox(" Track Layout")
        layout = QGridLayout(group)

        # Track width
        layout.addWidget(QLabel("Track Width (mm):"), 0, 0)
        self.track_width_spin = QDoubleSpinBox()
        self.track_width_spin.setRange(1.0, 10.0)
        self.track_width_spin.setValue(3.0)
        self.track_width_spin.setDecimals(1)
        self.track_width_spin.setSuffix(" mm")
        layout.addWidget(self.track_width_spin, 0, 1)

        # Track spacing
        layout.addWidget(QLabel("Track Spacing (mm):"), 1, 0)
        self.track_spacing_spin = QDoubleSpinBox()
        self.track_spacing_spin.setRange(0.5, 5.0)
        self.track_spacing_spin.setValue(1.5)
        self.track_spacing_spin.setDecimals(1)
        self.track_spacing_spin.setSuffix(" mm")
        layout.addWidget(self.track_spacing_spin, 1, 1)

        # Gap width
        layout.addWidget(QLabel("Gap Width (degrees):"), 2, 0)
        self.gap_width_spin = QDoubleSpinBox()
        self.gap_width_spin.setRange(0.5, 10.0)
        self.gap_width_spin.setValue(2.0)
        self.gap_width_spin.setDecimals(1)
        self.gap_width_spin.setSuffix("°")
        layout.addWidget(self.gap_width_spin, 2, 1)

        return group

    def create_control_buttons(self) -> QWidget:
        """Create control buttons section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Validation button
        self.validate_btn = QPushButton("🔍 Validate Parameters")
        self.validate_btn.clicked.connect(self.validate_parameters)
        layout.addWidget(self.validate_btn)

        # Optimization section
        opt_group = QGroupBox(" Genetic Optimization")
        opt_layout = QVBoxLayout(opt_group)

        # Optimization parameters
        opt_params_layout = QHBoxLayout()
        opt_params_layout.addWidget(QLabel("Generations:"))
        self.generations_spin = QSpinBox()
        self.generations_spin.setRange(10, 1000)
        self.generations_spin.setValue(100)
        opt_params_layout.addWidget(self.generations_spin)

        opt_params_layout.addWidget(QLabel("Population:"))
        self.population_spin = QSpinBox()
        self.population_spin.setRange(10, 100)
        self.population_spin.setValue(30)
        opt_params_layout.addWidget(self.population_spin)

        opt_layout.addLayout(opt_params_layout)

        # Optimization buttons
        self.optimize_btn = QPushButton(" Run Optimization")
        self.optimize_btn.clicked.connect(self.run_optimization)
        opt_layout.addWidget(self.optimize_btn)

        self.apply_opt_btn = QPushButton(" Apply Optimization")
        self.apply_opt_btn.clicked.connect(self.apply_optimization)
        self.apply_opt_btn.setEnabled(False)
        opt_layout.addWidget(self.apply_opt_btn)

        layout.addWidget(opt_group)

        # Generation section
        gen_group = QGroupBox(" Generation")
        gen_layout = QVBoxLayout(gen_group)

        self.generate_btn = QPushButton(" Generate SCAD File")
        self.generate_btn.clicked.connect(self.generate_encoder)
        gen_layout.addWidget(self.generate_btn)

        self.open_output_btn = QPushButton("📁 Open Output Folder")
        self.open_output_btn.clicked.connect(self.open_output_folder)
        gen_layout.addWidget(self.open_output_btn)

        layout.addWidget(gen_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return widget

    def create_right_panel(self) -> QWidget:
        """Create the right output panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Console output tab
        self.console_output = QTextEdit()
        self.console_output.setFont(QFont("Consolas", 14))
        # Note: QTextEdit doesn't have setMaximumBlockCount, use document instead
        self.console_output.document().setMaximumBlockCount(1000)
        self.tab_widget.addTab(self.console_output, "📋 Console")

        # Validation results tab
        self.validation_output = QTextEdit()
        self.validation_output.setFont(QFont("Consolas", 14))
        self.tab_widget.addTab(self.validation_output, " Validation")

        # Optimization results tab
        self.optimization_output = QTextEdit()
        self.optimization_output.setFont(QFont("Consolas", 14))
        self.tab_widget.addTab(self.optimization_output, " Optimization")

        # Initial welcome message
        self.log_message("🚢 Welcome to the Rudder Encoder Disk Generator!")
        self.log_message(
            "Set your physical parameters and click 'Validate Parameters' to start."
        )

        return panel

    def apply_styling(self):
        """Apply consistent styling to the application."""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 5px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QPushButton {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        QTextEdit {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
        }
        QTabWidget::pane {
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #4CAF50;
            color: white;
        }
        """
        self.setStyleSheet(style)

    def update_calculated_values(self):
        """Update calculated values when parameters change."""
        try:
            # Calculate outer diameter
            inner_radius = self.inner_radius_spin.value()
            encoder_width = self.encoder_width_spin.value()
            outer_diameter = (inner_radius + encoder_width) * 2
            self.outer_diameter_label.setText(f"{outer_diameter:.1f} mm")

            # Calculate tracks needed
            positions = int(self.positions_combo.currentText())
            import math

            tracks = math.ceil(math.log2(positions))
            self.tracks_label.setText(str(tracks))

            # Calculate angular resolution
            arc_angle = self.arc_angle_spin.value()
            resolution = arc_angle / positions
            self.resolution_label.setText(f"{resolution:.2f}°")

        except Exception as e:
            self.log_message(f" Error updating values: {e}")

    def get_current_parameters(self) -> Dict[str, Any]:
        """Get current parameter values from the GUI."""
        inner_radius = self.inner_radius_spin.value()
        encoder_width = self.encoder_width_spin.value()

        return {
            "outer_diameter_mm": (inner_radius + encoder_width) * 2,
            "inner_diameter_mm": inner_radius * 2,
            "disk_thickness_mm": self.thickness_spin.value(),
            "arc_angle_deg": self.arc_angle_spin.value(),
            "num_positions": int(self.positions_combo.currentText()),
            "num_tracks": int(self.tracks_label.text()),
            "track_width_mm": self.track_width_spin.value(),
            "track_spacing_mm": self.track_spacing_spin.value(),
            "gap_width_deg": self.gap_width_spin.value(),
            "bump_extension_mm": 5.0,
            "bump_width_deg": 3.0,
            "min_feature_size_mm": 0.16,  # Updated for 0.16mm line width
            "min_gap_size_mm": 0.2,  # Updated for 0.16mm capability
            "min_wall_thickness_mm": 0.32,  # Updated: 2 perimeters at 0.16mm
        }

    def load_default_parameters(self):
        """Load default parameters into the GUI."""
        self.update_calculated_values()
        self.log_message("📋 Default parameters loaded")

    def validate_parameters(self):
        """Validate current parameters."""
        self.log_message("🔍 Starting parameter validation...")
        self.validation_output.clear()

        # Get current parameters
        params = self.get_current_parameters()

        # Start validation worker
        self.validation_worker = ValidationWorker(params)
        self.validation_worker.finished.connect(self.on_validation_finished)
        self.validation_worker.error.connect(self.on_validation_error)
        self.validation_worker.start()

    def on_validation_finished(self, is_valid: bool, errors: list, warnings: list):
        """Handle validation results."""
        self.validation_output.clear()

        if is_valid:
            self.validation_output.append(" VALIDATION PASSED\n")
            self.validation_output.append(
                "All parameters meet manufacturing and functional constraints.\n"
            )
        else:
            self.validation_output.append(" VALIDATION FAILED\n")

        if errors:
            self.validation_output.append("🚫 ERRORS:")
            for error in errors:
                self.validation_output.append(f"  • {error}")
            self.validation_output.append("")

        if warnings:
            self.validation_output.append("  WARNINGS:")
            for warning in warnings:
                self.validation_output.append(f"  • {warning}")
            self.validation_output.append("")

        # Show summary
        params = self.get_current_parameters()
        self.validation_output.append(" PARAMETER SUMMARY:")
        self.validation_output.append(
            f"  • Outer diameter: {params['outer_diameter_mm']:.1f}mm"
        )
        self.validation_output.append(
            f"  • Arc angle: {params['arc_angle_deg']:.1f}°"
        )
        self.validation_output.append(f"  • Positions: {params['num_positions']}")
        self.validation_output.append(f"  • Tracks: {params['num_tracks']}")
        self.validation_output.append(
            f"  • Angular resolution: "
            f"{params['arc_angle_deg']/params['num_positions']:.2f}°"
        )

        # Switch to validation tab
        self.tab_widget.setCurrentIndex(1)

        self.log_message(f" Validation complete: {'PASSED' if is_valid else 'FAILED'}")

    def on_validation_error(self, error: str):
        """Handle validation error."""
        self.validation_output.setText(error)
        self.tab_widget.setCurrentIndex(1)
        self.log_message(error)

    def run_optimization(self):
        """Run genetic algorithm optimization."""
        self.log_message(" Starting genetic algorithm optimization...")
        self.optimization_output.clear()

        # Disable optimization button
        self.optimize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # Get current parameters
        params = self.get_current_parameters()
        generations = self.generations_spin.value()
        population = self.population_spin.value()

        # Start optimization worker
        self.optimization_worker = OptimizationWorker(params, generations, population)
        self.optimization_worker.progress.connect(self.on_optimization_progress)
        self.optimization_worker.finished.connect(self.on_optimization_finished)
        self.optimization_worker.error.connect(self.on_optimization_error)
        self.optimization_worker.start()

    def on_optimization_progress(self, message: str):
        """Handle optimization progress updates."""
        self.optimization_output.append(message)
        self.log_message(message)

    def on_optimization_finished(self, results: Dict[str, Any]):
        """Handle optimization completion."""
        self.optimization_results = results

        # Re-enable controls
        self.optimize_btn.setEnabled(True)
        self.apply_opt_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        # Display results
        self.optimization_output.append("\n OPTIMIZATION COMPLETE!\n")
        self.optimization_output.append(f"Best fitness: {results['fitness']:.3f}")
        self.optimization_output.append(f"Found in generation: {results['generation']}")
        self.optimization_output.append("\n FITNESS BREAKDOWN:")

        for component, value in results["fitness_components"].items():
            self.optimization_output.append(f"  • {component}: {value:.3f}")

        self.optimization_output.append("\n OPTIMIZED PARAMETERS:")
        params = results["parameters"]
        self.optimization_output.append(
            f"  • Outer diameter: {params['outer_diameter_mm']:.1f}mm"
        )
        self.optimization_output.append(
            f"  • Arc angle: {params['arc_angle_deg']:.1f}°"
        )
        self.optimization_output.append(f"  • Positions: {params['num_positions']}")
        self.optimization_output.append(
            f"  • Track width: {params['track_width_mm']:.1f}mm"
        )
        self.optimization_output.append(
            f"  • Gap width: {params['gap_width_deg']:.1f}°"
        )

        # Switch to optimization tab
        self.tab_widget.setCurrentIndex(2)

        self.log_message(f"🎉 Optimization complete! Fitness: {results['fitness']:.3f}")

    def on_optimization_error(self, error: str):
        """Handle optimization error."""
        self.optimize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.optimization_output.setText(error)
        self.tab_widget.setCurrentIndex(2)
        self.log_message(error)

    def apply_optimization(self):
        """Apply optimization results to current parameters."""
        if not self.optimization_results:
            QMessageBox.warning(self, "No Results", "No optimization results to apply!")
            return

        try:
            params = self.optimization_results["parameters"]

            # Update GUI with optimized parameters
            outer_diameter = params["outer_diameter_mm"]
            inner_diameter = params["inner_diameter_mm"]

            # Calculate the required values for the GUI
            inner_radius = inner_diameter / 2
            encoder_width = (outer_diameter - inner_diameter) / 2

            self.inner_radius_spin.setValue(inner_radius)
            self.encoder_width_spin.setValue(encoder_width)
            self.arc_angle_spin.setValue(params["arc_angle_deg"])
            self.thickness_spin.setValue(params["disk_thickness_mm"])
            self.positions_combo.setCurrentText(str(params["num_positions"]))
            self.track_width_spin.setValue(params["track_width_mm"])
            self.track_spacing_spin.setValue(params["track_spacing_mm"])
            self.gap_width_spin.setValue(params["gap_width_deg"])

            self.update_calculated_values()

            self.log_message(" Optimization results applied to parameters")

            # Auto-validate after applying
            self.validate_parameters()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply optimization: {e}")
            self.log_message(f" Failed to apply optimization: {e}")

    def generate_encoder(self):
        """Generate the encoder SCAD file."""
        self.log_message(" Generating encoder SCAD file...")

        try:
            # Get current parameters
            params = self.get_current_parameters()

            # Save parameters to temporary file
            output_dir = self.project_root / "output"
            output_dir.mkdir(exist_ok=True)

            params_file = output_dir / "gui_parameters.json"
            with open(params_file, "w") as f:
                json.dump(params, f, indent=2)

            # Run the encoder generator
            cmd = [
                "poetry",
                "run",
                "python",
                "src/encoder_generator.py",
                "--output",
                str(output_dir / "gui_encoder.scad"),
                "--config",
                "custom",
                "--params",
                str(params_file),
            ]

            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )

            if result.returncode == 0:
                self.log_message(" Encoder SCAD file generated successfully!")
                self.log_message(f"📁 Output: {output_dir / 'gui_encoder.scad'}")

                # Show success message
                QMessageBox.information(
                    self,
                    "Success",
                    f"Encoder SCAD file generated successfully!\n\n"
                    f"Location: {output_dir / 'gui_encoder.scad'}",
                )
            else:
                error_msg = result.stderr or result.stdout
                self.log_message(f" Generation failed: {error_msg}")
                QMessageBox.critical(self, "Error", f"Generation failed:\n{error_msg}")

        except Exception as e:
            error_msg = f"Failed to generate encoder: {e}"
            self.log_message(f" {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)

    def open_output_folder(self):
        """Open the output folder in file manager."""
        output_dir = self.project_root / "output"
        output_dir.mkdir(exist_ok=True)

        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(output_dir)])
            elif sys.platform == "win32":  # Windows
                subprocess.run(["explorer", str(output_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(output_dir)])

            self.log_message(f"📁 Opened output folder: {output_dir}")

        except Exception as e:
            self.log_message(f" Failed to open folder: {e}")

    def log_message(self, message: str):
        """Add a message to the console log."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_output.append(f"[{timestamp}] {message}")

        # Auto-scroll to bottom
        scrollbar = self.console_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Rudder Encoder Disk Generator")

    # Create and show the main window
    window = EncoderControllerGUI()
    window.show()

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
