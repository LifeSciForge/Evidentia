"""
LLM initialization and configuration
Handles model selection, initialization, and model management
"""

from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.core.settings import settings


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def invoke_with_retry(llm, prompt):
    """Call llm.invoke(prompt) with up to 3 attempts + exponential backoff.
    Callers wrap this in asyncio.to_thread to keep the event loop free."""
    return llm.invoke(prompt)


class LLMManager:
    """Manages LLM initialization and caching"""

    # Per-config cache: key = (model, temperature, max_tokens)
    _claude_instances: dict = {}
    _openai_instance: Optional[ChatOpenAI] = None

    @classmethod
    def get_claude(
        cls,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatAnthropic:
        """
        Get Claude model instance (cached per distinct config).

        Args:
            model: Model name; defaults to settings.DEFAULT_MODEL when None
            temperature: Temperature for sampling (0-1)
            max_tokens: Maximum tokens in response

        Returns:
            Initialized ChatAnthropic instance
        """
        model = model or settings.DEFAULT_MODEL
        key = (model, temperature, max_tokens)
        if key not in cls._claude_instances:
            cls._claude_instances[key] = ChatAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        return cls._claude_instances[key]

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
    """Get Claude model (cached per distinct config).

    Usage:
        from src.core.llm import get_claude
        llm = get_claude(temperature=0.3)   # factual extraction
        llm = get_claude(temperature=0.7)   # synthesis / creative
    """
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
