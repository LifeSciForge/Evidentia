"""
Evidentia - MSL Intelligence Platform
Entry point for Streamlit Cloud deployment
"""

import sys
from pathlib import Path

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Run the main app
from ui.app import main

if __name__ == "__main__":
    main()
