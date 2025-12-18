#!/usr/bin/env python3
"""
Android Log Monitor - Main Entry Point

A cross-platform desktop GUI application for real-time Android device log monitoring and analysis via ADB.
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def main():
    """Main application entry point"""
    try:
        # Import GUI after path setup
        from src.gui_main import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
