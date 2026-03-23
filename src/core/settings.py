"""
Configuration and settings management for GTM Simulator
Handles environment variables, API keys, and configuration
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # ========================================================================
    # LLM Configuration
    # ========================================================================
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"
    
    # ========================================================================
    # Ollama Configuration (Local LLM)
    # ========================================================================
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    
    # ========================================================================
    # API Keys for Research
    # ========================================================================
    TAVILY_API_KEY: str
    
    # ========================================================================
    # Server Configuration
    # ========================================================================
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8080
    FASTAPI_RELOAD: bool = True
    
    STREAMLIT_SERVER_PORT: int = 8501
    STREAMLIT_SERVER_ADDRESS: str = "0.0.0.0"
    
    # ========================================================================
    # Database & Caching
    # ========================================================================
    USE_MEMORY_CACHE: bool = True
    REDIS_URL: Optional[str] = None
    DATABASE_URL: Optional[str] = "sqlite:///./gtm_simulator.db"
    
    # ========================================================================
    # Logging
    # ========================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/gtm_simulator.log"
    
    # ========================================================================
    # Agent Configuration
    # ========================================================================
    AGENT_TIMEOUT: int = 300  # 5 minutes per agent
    STREAMING_ENABLED: bool = True
    
    # ========================================================================
    # Authentication (Optional)
    # ========================================================================
    AUTH_SECRET: Optional[str] = None
    SESSION_TIMEOUT: int = 3600  # 1 hour
    
    # ========================================================================
    # LangSmith (Optional - for tracing)
    # ========================================================================
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "gtm-simulator"
    LANGSMITH_TRACING: bool = False
    
    # ========================================================================
    # Sentry (Optional - for error tracking)
    # ========================================================================
    SENTRY_DSN: Optional[str] = None
    
    # ========================================================================
    # Development
    # ========================================================================
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    class Config:
        """Pydantic config"""
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses caching to avoid reloading .env file multiple times.
    """
    return Settings()


# Export for easy import
settings = get_settings()


# ============================================================================
# Utility Functions
# ============================================================================

def validate_settings():
    """Validate that all required settings are present"""
    required = ["ANTHROPIC_API_KEY", "TAVILY_API_KEY"]
    missing = [key for key in required if not getattr(settings, key, None)]
    
    if missing:
        raise ValueError(f"Missing required settings: {', '.join(missing)}")


def get_api_keys_status() -> dict:
    """Return status of configured API keys"""
    return {
        "anthropic": "✅ Configured" if settings.ANTHROPIC_API_KEY else "❌ Missing",
        "tavily": "✅ Configured" if settings.TAVILY_API_KEY else "❌ Missing",
        "ollama": "✅ Configured" if settings.OLLAMA_BASE_URL else "⚠️ Optional",
        "langsmith": "✅ Configured" if settings.LANGSMITH_API_KEY else "⚠️ Optional",
    }


if __name__ == "__main__":
    # Quick validation when run directly
    try:
        validate_settings()
        print("✅ All required settings configured!")
        print("\nAPI Keys Status:")
        for key, status in get_api_keys_status().items():
            print(f"  {key}: {status}")
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")