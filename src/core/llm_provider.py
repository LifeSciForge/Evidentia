"""
LLM Provider - Uses Ollama (local, free, zero API cost)
"""

import os
import requests
import json
from typing import Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers"""
    OLLAMA_MISTRAL = "ollama_mistral"
    OLLAMA_LLAMA2 = "ollama_llama2"


class LLMClient:
    """
    LLM client using Ollama (local inference, zero cost)
    """
    
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or LLMProvider.OLLAMA_MISTRAL
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        logger.info(f"🚀 LLM Client initialized: {self.provider.value}")
    
    def invoke(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Invoke LLM using Ollama (runs locally, zero cost)
        """
        
        try:
            if self.provider == LLMProvider.OLLAMA_MISTRAL:
                model = "mistral"
            elif self.provider == LLMProvider.OLLAMA_LLAMA2:
                model = "llama2"
            else:
                model = "mistral"
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_k": 40,
                        "top_p": 0.9,
                    }
                },
                timeout=180
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Ollama error: {response.text}")
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"❌ Cannot connect to Ollama at {self.ollama_url}\n"
                f"Start Ollama with: ollama serve"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama error: {str(e)}")


def get_llm(provider: Optional[LLMProvider] = None) -> LLMClient:
    """Get LLM client (uses Ollama by default)"""
    return LLMClient(provider=provider)


if __name__ == "__main__":
    print("Testing LLM Client...")
    try:
        llm = get_llm()
        response = llm.invoke("What is drug discovery in one sentence?")
        print(f"✅ Response: {response[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
