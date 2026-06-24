"""
Evidentia - MSL Intelligence Platform
Entry point for Streamlit Cloud deployment
"""

import os
import sys
from pathlib import Path

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
from src.core.preflight import missing_required_secrets

# Pre-flight: fail clearly (not a white-screen crash) if required secrets are absent.
_missing = missing_required_secrets(os.environ)
if _missing:
    st.set_page_config(page_title="Evidentia — Configuration needed", page_icon="🏥")
    st.error("⚠️ Evidentia isn't configured yet.")
    st.markdown(
        "Missing required secret(s): **"
        + ", ".join(_missing)
        + "**.\n\nAdd them in Streamlit Cloud → **Manage app → Settings → Secrets** "
        "(flat, top-level keys), then reboot."
    )
    st.stop()

# Run the main app
from ui.app import main

st.markdown("""<style>
.main > div { max-width: 100% !important; }
.block-container { max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; padding-top: 1rem !important; }
div[data-testid="stMainBlockContainer"] { max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
</style>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
