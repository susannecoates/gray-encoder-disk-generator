#!/usr/bin/env python3
"""
GUI Launcher for Rudder Encoder Disk Generator

Simple launcher script for the PyQt6 GUI interface.
Use: poetry run python launch_gui.py
"""

import sys
import os
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from gui_encoder_controller import main
    main()
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure to run with: poetry run python launch_gui.py")
    print("Or install PyQt6: poetry add PyQt6")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error launching GUI: {e}")
    sys.exit(1)
