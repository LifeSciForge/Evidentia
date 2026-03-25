"""
Debug script to catch startup errors
"""
import sys
import traceback

print("=" * 80)
print("EVIDENTIA STARTUP DEBUG")
print("=" * 80)

try:
    print("\n1. Testing basic imports...")
    import streamlit as st
    print("   ✓ streamlit imported")
    
    import pandas as pd
    print("   ✓ pandas imported")
    
    print("\n2. Testing src imports...")
    from src.core.logger import get_logger
    print("   ✓ logger imported")
    
    print("\n3. Testing LangGraph import (THE HEAVY ONE)...")
    from src.agents.gtm_workflow import create_gtm_workflow
    print("   ✓ gtm_workflow imported")
    
    print("\n4. Creating workflow...")
    workflow = create_gtm_workflow()
    print("   ✓ workflow created")
    
    print("\n✅ ALL IMPORTS SUCCESSFUL!")
    print("=" * 80)
    
except Exception as e:
    print("\n❌ ERROR DETECTED!")
    print("=" * 80)
    print(f"\nError Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")
    print("\nFull Traceback:")
    traceback.print_exc()
    print("=" * 80)
    sys.exit(1)
