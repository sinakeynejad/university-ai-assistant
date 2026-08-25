"""
LLM layer - Direct Ollama API client.

Two implementations are available:
1. MockLLMClient: Used for initial frontend/backend testing without an API key.
2. OllamaLLMClient: Direct HTTP client for Ollama's chat completion API.

The implementation is selected through the LLM_PROVIDER setting in .env.
"""

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List, Dict, Generator, Optional
import json
import time
import httpx

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None, timeout: Optional[float] = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """Test client that does not require a real LLM or API key."""
    def generate(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None, timeout: Optional[float] = None) -> str:
        user_message = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            ""
        )
        return (
            "[Test response - real LLM is not connected]\n"
            "This is a mock response used to verify that the RAG pipeline "
            "(document retrieval) is working correctly. To use a real LLM, "
            "set LLM_PROVIDER to 'ollama' in the .env file.\n\n"
            f"Received question: {user_message}"
        )

    def generate_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        full_text = self.generate(messages)
        for word in full_text.split(" "):
            yield word + " "
            time.sleep(0.03)


class OllamaLLMClient(BaseLLMClient):
    """Direct HTTP client for Ollama's /api/chat endpoint."""

    def __init__(
        self,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)

    def _prepare_payload(self, messages: List[Dict[str, str]], stream: bool = False, max_tokens: Optional[int] = None):
        """Prepare the request payload for Ollama's /api/chat endpoint."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": max_tokens or self.max_tokens,
            },
        }
        return payload

    def generate(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None, timeout: Optional[float] = None) -> str:
        """Send a non-streaming request to Ollama."""
        url = f"{self.base_url}/api/chat"
        payload = self._prepare_payload(messages, stream=False, max_tokens=max_tokens)
        
        try:
            resp = self.client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Ollama returns a single message in the 'message' field when stream=False
            if "message" in data and "content" in data["message"]:
                return data["message"]["content"]
            else:
                logger.warning("Unexpected response format from Ollama: %s", data)
                return ""
        except httpx.TimeoutException:
            logger.warning("Ollama request timed out.")
            return ""
        except Exception as e:
            logger.warning(f"Ollama request failed: {e}")
            return ""

    def generate_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Stream responses from Ollama."""
        url = f"{self.base_url}/api/chat"
        payload = self._prepare_payload(messages, stream=True)
        
        try:
            with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
                        # Check for final 'done' message (optional)
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse Ollama stream line: {line} - {e}")
        except httpx.TimeoutException:
            logger.warning("Ollama streaming request timed out.")
            yield "خطا: زمان پاسخ‌دهی به پایان رسید."
        except Exception as e:
            logger.warning(f"Ollama streaming request failed: {e}")
            yield f"خطا: {e}"


@lru_cache
def get_llm_client() -> BaseLLMClient:
    settings = get_settings()
    provider = settings.LLM_PROVIDER

    if provider == "openai_compatible" or provider == "ollama":
        # If base_url is Ollama's default, use the direct client.
        if "localhost:11434" in settings.LLM_BASE_URL or "127.0.0.1:11434" in settings.LLM_BASE_URL:
            logger.info(f"Using OllamaLLMClient with base_url={settings.LLM_BASE_URL}, model={settings.LLM_MODEL_NAME}")
            return OllamaLLMClient(
                base_url=settings.LLM_BASE_URL,
                model=settings.LLM_MODEL_NAME,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
        else:
            # Fallback to the original OpenAI-compatible client if needed.
            # But since we're removing openai, we'll just log and raise.
            logger.warning("LLM_PROVIDER=openai_compatible but not Ollama; falling back to mock.")
            return MockLLMClient()

    # Default mock
    logger.info("Using MockLLMClient (test mode without a real LLM).")
    return MockLLMClient()