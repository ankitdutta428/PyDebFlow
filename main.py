#!/usr/bin/env python
"""
PyDebFlow - Mass Flow Simulation Tool
r.avaflow Replica

Main entry point for the GUI application.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Launch the PyDebFlow GUI application."""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from src.gui.main_window import MainWindow
        
        # Enable High DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        app = QApplication(sys.argv)
        app.setApplicationName("PyDebFlow")
        app.setOrganizationName("PyDebFlow")
        app.setApplicationVersion("0.1.0")
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
        
    except ImportError as e:
        print("=" * 60)
        print("PyDebFlow - GUI Error")
        print("=" * 60)
        print(f"\nError: {e}")
        print("\nThe GUI requires PyQt6. Please install it with:")
        print("  pip install PyQt6")
        print("\nAlternatively, you can run simulations from command line:")
        print("  python run_simulation.py --synthetic-test")
        print("\nOr use the CLI:")
        print("  python -m src.cli run --synthetic --t-end 60")
        sys.exit(1)


if __name__ == '__main__':
    main()
