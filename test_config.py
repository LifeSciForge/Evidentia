#!/usr/bin/env python3
"""Test script to verify configuration"""

import sys
from src.core.settings import settings, validate_settings, get_api_keys_status
from src.core.logger import get_logger, logger
from src.core.llm import get_model

def main():
    """Run configuration tests"""
    print("=" * 60)
    print("GTM SIMULATOR - CONFIGURATION TEST")
    print("=" * 60)
    
    # Test 1: Settings validation
    print("\n1️⃣  Validating settings...")
    try:
        validate_settings()
        print("✅ All required settings found!")
    except ValueError as e:
        print(f"❌ Validation failed: {e}")
        return False
    
    # Test 2: API keys status
    print("\n2️⃣  API Keys Status:")
    for key, status in get_api_keys_status().items():
        print(f"   {key}: {status}")
    
    # Test 3: Logger
    print("\n3️⃣  Testing logger...")
    logger.info("✅ Logger initialized successfully")
    print(f"   Logs saved to: {settings.LOG_FILE}")
    
    # Test 4: LLM
    print("\n4️⃣  Initializing LLM...")
    try:
        model = get_model()
        print(f"✅ Model initialized: {model.model}")
    except Exception as e:
        print(f"❌ LLM error: {e}")
        return False
    
    # Test 5: Application info
    print("\n5️⃣  Application Configuration:")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug: {settings.DEBUG}")
    print(f"   Log Level: {settings.LOG_LEVEL}")
    print(f"   Streaming: {settings.STREAMING_ENABLED}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Ready to build!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)