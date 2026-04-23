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
import streamlit as st

st.markdown("""<style>
.main > div { max-width: 100% !important; }
.block-container { max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; padding-top: 1rem !important; }
div[data-testid="stMainBlockContainer"] { max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
</style>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
