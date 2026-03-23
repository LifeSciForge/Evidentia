"""
LLM initialization and configuration
Handles model selection, initialization, and model management
"""

from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from src.core.settings import settings


class LLMManager:
    """Manages LLM initialization and caching"""
    
    _claude_instance: Optional[ChatAnthropic] = None
    _openai_instance: Optional[ChatOpenAI] = None

    @classmethod
    def get_claude(
        cls,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatAnthropic:
        """
        Get Claude model instance (cached)
        
        Args:
            model: Model name (default: claude-sonnet-4-20250514)
            temperature: Temperature for sampling (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            Initialized ChatAnthropic instance
        """
        if cls._claude_instance is None:
            cls._claude_instance = ChatAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        return cls._claude_instance

    @classmethod
    def get_openai(
        cls,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatOpenAI:
        """
        Get OpenAI model instance (cached)
        
        Args:
            model: Model name (default: gpt-4)
            temperature: Temperature for sampling (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            Initialized ChatOpenAI instance
        """
        if cls._openai_instance is None:
            cls._openai_instance = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        return cls._openai_instance

    @classmethod
    def get_model(
        cls,
        model_name: Optional[str] = None,
        **kwargs,
    ) -> BaseChatModel:
        """
        Get any model by name
        
        Args:
            model_name: Model name or identifier
            **kwargs: Additional arguments for model initialization
            
        Returns:
            Initialized model instance
        """
        if model_name is None:
            model_name = settings.DEFAULT_MODEL

        # Route to appropriate model
        if "claude" in model_name.lower():
            return cls.get_claude(model=model_name, **kwargs)
        elif "gpt" in model_name.lower():
            return cls.get_openai(model=model_name, **kwargs)
        else:
            # Default to Claude
            return cls.get_claude(model=model_name, **kwargs)


# ============================================================================
# Convenience Functions
# ============================================================================

def get_model(
    model_name: Optional[str] = None,
    **kwargs,
) -> BaseChatModel:
    """
    Get a model instance
    
    Usage:
        from src.core.llm import get_model
        model = get_model()  # Uses default (Claude Sonnet)
        response = model.invoke("What is 2+2?")
    """
    return LLMManager.get_model(model_name, **kwargs)


def get_claude(**kwargs) -> ChatAnthropic:
    """Get Claude model"""
    return LLMManager.get_claude(**kwargs)


def get_openai(**kwargs) -> ChatOpenAI:
    """Get OpenAI model"""
    return LLMManager.get_openai(**kwargs)


if __name__ == "__main__":
    # Test LLM initialization
    try:
        print("🧠 Initializing Claude Sonnet...")
        model = get_claude()
        print(f"✅ Claude initialized: {model.model}")
        
        print("\n🧪 Testing model...")
        response = model.invoke("Say 'Hello from GTM Simulator!' in one sentence.")
        print(f"Response: {response.content}")
        
    except Exception as e:
        print(f"❌ Error: {e}")