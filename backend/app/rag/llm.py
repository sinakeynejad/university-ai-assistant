"""
LLM layer.

Two implementations are available:
1. MockLLMClient: Used for initial frontend/backend testing without an API key.
2. OpenAICompatibleClient: Works with OpenAI-compatible Chat Completions APIs.

The implementation is selected through the LLM_PROVIDER setting in .env.
"""

from abc import ABC, abstractmethod
from functools import lru_cache

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

try:
    from app.config import get_settings
    from app.utils.logger import get_logger
except ModuleNotFoundError:  # pragma: no cover - supports repo-root execution
    from backend.app.config import get_settings
    from backend.app.utils.logger import get_logger


# Initialize application logger
logger = get_logger(__name__)


class BaseLLMClient(ABC):

    @abstractmethod
    def generate(self, messages: list[ChatCompletionMessageParam]) -> str:
        """Generate a response from the provided chat messages."""
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    """
    Test client that does not require a real LLM or API key.

    It returns a simple mock response so the complete RAG pipeline
    can be tested from frontend to backend and retrieval.
    """

    def generate(self, messages: list[ChatCompletionMessageParam]) -> str:

        # Find the latest user message in a way that is compatible with OpenAI's
        # typed message structure and may contain list-based content payloads.
        user_message = ""
        for message in reversed(messages):
            if not isinstance(message, dict):
                continue
            if message.get("role") != "user":
                continue

            content = message.get("content")
            if isinstance(content, str):
                user_message = content
                break
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text")
                        if isinstance(text, str):
                            text_parts.append(text)
                if text_parts:
                    user_message = " ".join(text_parts)
                    break
            break

        # Return a mock response instead of calling a real LLM
        return (
            "[Test response - real LLM is not connected]\n"
            "This is a mock response used to verify that the RAG pipeline "
            "(document retrieval) is working correctly. To use a real LLM, "
            "set LLM_PROVIDER to 'openai_compatible' and configure "
            "LLM_API_KEY in the .env file.\n\n"
            f"Received question: {user_message}"
        )


class OpenAICompatibleClient(BaseLLMClient):

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int
    ):
        # Create an OpenAI-compatible API client
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, messages: list[ChatCompletionMessageParam]) -> str:

        # Send the messages to the configured LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        # Return the generated text
        return response.choices[0].message.content or ""


@lru_cache
def get_llm_client() -> BaseLLMClient:
    # Load application settings
    settings = get_settings()

    # Use the real LLM client if configured
    if settings.LLM_PROVIDER == "openai_compatible":

        # Warn if the API key is missing
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

    # Otherwise, use the mock client for testing
    logger.info(
        "Using MockLLMClient (test mode without a real LLM)."
    )

    return MockLLMClient()
