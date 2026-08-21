"""
LLM layer.

Two implementations are available:
1. MockLLMClient: Used for initial frontend/backend testing without an API key.
2. OpenAICompatibleClient: Works with OpenAI-compatible Chat Completions APIs.

The implementation is selected through the LLM_PROVIDER setting in .env.
"""

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List, Dict, Generator
import time

from openai import OpenAI

from app.config import get_settings
from app.utils.logger import get_logger


# Initialize application logger
logger = get_logger(__name__)


class BaseLLMClient(ABC):

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]]) -> str:
        """Generate a response from the provided chat messages."""
        raise NotImplementedError

    @abstractmethod
    def generate_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Generate a response stream chunk-by-chunk."""
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """
    Test client that does not require a real LLM or API key.

    It returns a simple mock response so the complete RAG pipeline
    can be tested from frontend to backend and retrieval.
    """

    def generate(self, messages: List[Dict[str, str]]) -> str:
        user_message = next(
            (
                m["content"]
                for m in reversed(messages)
                if m["role"] == "user"
            ),
            ""
        )

        return (
            "[Test response - real LLM is not connected]\n"
            "This is a mock response used to verify that the RAG pipeline "
            "(document retrieval) is working correctly. To use a real LLM, "
            "set LLM_PROVIDER to 'openai_compatible' and configure "
            "LLM_API_KEY in the .env file.\n\n"
            f"Received question: {user_message}"
        )

    def generate_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Simulate streaming response word by word for mock testing."""
        full_text = self.generate(messages)
        for word in full_text.split(" "):
            yield word + " "
            time.sleep(0.03)


class OpenAICompatibleClient(BaseLLMClient):

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content

    def generate_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Stream chunks directly from OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True 
            )

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error in OpenAI LLM streaming: {e}")
            raise e


@lru_cache
def get_llm_client() -> BaseLLMClient:
    settings = get_settings()

    if settings.LLM_PROVIDER == "openai_compatible":
        if not settings.LLM_API_KEY:
            logger.warning(
                "LLM_API_KEY is empty; requests are likely to fail."
            )

        return OpenAICompatibleClient(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL_NAME,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

    logger.info(
        "Using MockLLMClient (test mode without a real LLM)."
    )

    return MockLLMClient()