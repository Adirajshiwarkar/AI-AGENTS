import os
from abc import ABC, abstractmethod
from utils.logger import logger

class LLMProvider(ABC):
    """Abstract interface for all LLM client implementations."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generates a text completion based on the prompt."""
        pass

class LLMFactory:
    """Factory to initialize and cache the appropriate LLM client."""
    
    def __init__(self):
        self._cached_client: LLMProvider = None

    def get_client(self) -> LLMProvider:
        """Resolves the LLM client according to LLM_PROVIDER in .env (ollama, gemini, groq)."""
        if self._cached_client:
            return self._cached_client

        provider_type = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

        if provider_type == "ollama":
            from llm.ollama_client import OllamaProvider
            logger.info("Initializing local Ollama LLM Provider...")
            self._cached_client = OllamaProvider()
        elif provider_type == "gemini":
            from llm.gemini_client import GeminiProvider
            logger.info("Initializing Gemini LLM Provider...")
            self._cached_client = GeminiProvider()
        elif provider_type == "groq":
            from llm.groq_client import GroqProvider
            logger.info("Initializing Groq LLM Provider...")
            self._cached_client = GroqProvider()
        else:
            from llm.ollama_client import OllamaProvider
            logger.warning(f"Unknown LLM provider '{provider_type}'. Defaulting to local Ollama.")
            self._cached_client = OllamaProvider()

        return self._cached_client




