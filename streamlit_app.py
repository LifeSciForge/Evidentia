"""
Entry point for Streamlit app
Run with: streamlit run streamlit_app.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.app import main

if __name__ == "__main__":
    main()
