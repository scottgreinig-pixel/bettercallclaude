"""
Ollama integration for local LLM inference.

Provides privacy-first AI capabilities for sensitive legal work,
with graceful fallback to Claude when needed.
"""

import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OllamaModel(Enum):
    """Supported Ollama models for legal work."""

    # Best overall reasoning - recommended for complex legal analysis
    LLAMA3_70B = "llama3.1:70b"
    LLAMA3_8B = "llama3.1:8b"

    # Good balance of speed/quality
    MIXTRAL = "mixtral:8x7b"

    # Efficient for simple tasks
    PHI3 = "phi3:medium"

    # Multilingual support (important for Swiss DE/FR/IT)
    LLAMA3_2_3B = "llama3.2:3b"

    # Code-focused models
    CODELLAMA = "codellama:13b"

    @property
    def recommended_for(self) -> str:
        """Get recommended use case for this model."""
        recommendations: dict[OllamaModel, str] = {
            OllamaModel.LLAMA3_70B: "Complex legal analysis, document review, strategic reasoning",
            OllamaModel.LLAMA3_8B: "General tasks, quick responses, Swiss German processing",
            OllamaModel.MIXTRAL: "Balanced quality/speed, multilingual support",
            OllamaModel.PHI3: "Simple tasks, fast responses, low resource usage",
            OllamaModel.LLAMA3_2_3B: "Mobile/edge deployment, basic queries",
            OllamaModel.CODELLAMA: "Code generation, technical documentation",
        }
        return recommendations.get(self, "General purpose")

    @property
    def context_length(self) -> int:
        """Return approximate context window size."""
        context_sizes: dict[OllamaModel, int] = {
            OllamaModel.LLAMA3_70B: 128000,
            OllamaModel.LLAMA3_8B: 128000,
            OllamaModel.MIXTRAL: 32000,
            OllamaModel.PHI3: 4096,
            OllamaModel.LLAMA3_2_3B: 128000,
            OllamaModel.CODELLAMA: 16000,
        }
        return context_sizes.get(self, 4096)


@dataclass
class OllamaConfig:
    """Ollama connection configuration."""

    host: str = "http://localhost:11434"
    timeout: float = 120.0
    default_model: OllamaModel = OllamaModel.LLAMA3_8B
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True
    custom_headers: dict[str, str] = field(default_factory=dict)


@dataclass
class OllamaResponse:
    """Structured response from Ollama."""

    content: str
    model: str
    tokens_used: int
    prompt_tokens: int
    generation_time: float
    is_complete: bool
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def tokens_per_second(self) -> float:
        """Calculate generation speed."""
        if self.generation_time > 0:
            return self.tokens_used / self.generation_time
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "prompt_tokens": self.prompt_tokens,
            "generation_time": self.generation_time,
            "is_complete": self.is_complete,
            "created_at": self.created_at.isoformat(),
            "tokens_per_second": self.tokens_per_second,
        }


@dataclass
class ChatMessage:
    """Chat message for conversation history."""

    role: str  # "system", "user", "assistant"
    content: str

    def to_dict(self) -> dict[str, str]:
        """Convert to API format."""
        return {"role": self.role, "content": self.content}


class OllamaUnavailableError(Exception):
    """Raised when Ollama is not available."""

    pass


class OllamaModelNotFoundError(Exception):
    """Raised when requested model is not available."""

    pass


class OllamaClient:
    """
    Client for Ollama local LLM inference.

    Features:
    - Automatic model selection based on task
    - Streaming response support
    - Health checking and availability detection
    - Graceful degradation when unavailable
    - Swiss multilingual support (DE/FR/IT)
    """

    def __init__(self, config: OllamaConfig | None = None):
        """Initialize Ollama client.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or OllamaConfig()
        self._http_client: httpx.AsyncClient | None = None
        self._available: bool | None = None
        self._available_models: list[str] = []
        self._last_health_check: datetime | None = None

    async def __aenter__(self) -> "OllamaClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                headers=self.config.custom_headers,
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def is_available(self, force_check: bool = False) -> bool:
        """Check if Ollama is running and accessible.

        Args:
            force_check: If True, bypass cache and check again.

        Returns:
            True if Ollama is available and responding.
        """
        # Return cached result if recent (within 30 seconds)
        if (
            not force_check
            and self._available is not None
            and self._last_health_check
            and (datetime.now() - self._last_health_check).seconds < 30
        ):
            return self._available

        await self._ensure_client()
        assert self._http_client is not None  # for type checker

        try:
            response = await self._http_client.get(f"{self.config.host}/api/tags")
            if response.status_code == 200:
                self._available = True
                data = response.json()
                self._available_models = [m["name"] for m in data.get("models", [])]
                self._last_health_check = datetime.now()
                logger.debug(f"Ollama available with {len(self._available_models)} models")
                return True
        except httpx.ConnectError:
            logger.warning("Ollama not available: Connection refused")
        except httpx.TimeoutException:
            logger.warning("Ollama not available: Connection timeout")
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")

        self._available = False
        self._last_health_check = datetime.now()
        return False

    async def list_models(self) -> list[str]:
        """List available models.

        Returns:
            List of model names available on the Ollama server.
        """
        if not await self.is_available():
            return []
        return self._available_models

    async def has_model(self, model: OllamaModel | str) -> bool:
        """Check if a specific model is available.

        Args:
            model: Model enum or string name to check.

        Returns:
            True if model is available locally.
        """
        if not await self.is_available():
            return False

        model_name = model.value if isinstance(model, OllamaModel) else model

        # Check exact match or prefix match (handles version tags)
        for available in self._available_models:
            if available == model_name or available.startswith(model_name.split(":")[0]):
                return True
        return False

    async def generate(
        self,
        prompt: str,
        model: OllamaModel | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.9,
        stop_sequences: list[str] | None = None,
    ) -> OllamaResponse:
        """Generate completion from Ollama.

        Args:
            prompt: User prompt to generate from.
            model: Model to use (default from config).
            system_prompt: Optional system prompt for context.
            temperature: Sampling temperature (0.0-1.0).
            max_tokens: Maximum tokens to generate.
            top_p: Nucleus sampling parameter.
            stop_sequences: Stop generation at these sequences.

        Returns:
            OllamaResponse with generated content.

        Raises:
            OllamaUnavailableError: If Ollama is not available.
            OllamaModelNotFoundError: If requested model is not available.
        """
        if not await self.is_available():
            raise OllamaUnavailableError("Ollama is not available")

        model_enum = model or self.config.default_model
        model_name = model_enum.value

        # Check if model is available
        if not await self.has_model(model_enum):
            raise OllamaModelNotFoundError(
                f"Model {model_name} not found. Available: {self._available_models}"
            )

        await self._ensure_client()
        assert self._http_client is not None

        payload: dict[str, Any] = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        if stop_sequences:
            payload["options"]["stop"] = stop_sequences

        response = await self._http_client.post(
            f"{self.config.host}/api/generate",
            json=payload,
        )

        if response.status_code != 200:
            raise OllamaUnavailableError(
                f"Ollama API error: {response.status_code} - {response.text}"
            )

        data = response.json()

        return OllamaResponse(
            content=data.get("response", ""),
            model=model_name,
            tokens_used=data.get("eval_count", 0),
            prompt_tokens=data.get("prompt_eval_count", 0),
            generation_time=data.get("total_duration", 0) / 1e9,  # ns to seconds
            is_complete=data.get("done", False),
        )

    async def generate_stream(
        self,
        prompt: str,
        model: OllamaModel | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Stream generation token by token.

        Args:
            prompt: User prompt to generate from.
            model: Model to use (default from config).
            system_prompt: Optional system prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Yields:
            Individual tokens/chunks as they are generated.

        Raises:
            OllamaUnavailableError: If Ollama is not available.
        """
        if not await self.is_available():
            raise OllamaUnavailableError("Ollama is not available")

        model_enum = model or self.config.default_model
        model_name = model_enum.value

        await self._ensure_client()
        assert self._http_client is not None

        payload: dict[str, Any] = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        async with self._http_client.stream(
            "POST",
            f"{self.config.host}/api/generate",
            json=payload,
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    import json

                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

    async def chat(
        self,
        messages: list[ChatMessage],
        model: OllamaModel | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> OllamaResponse:
        """Chat completion with message history.

        Args:
            messages: List of chat messages (conversation history).
            model: Model to use (default from config).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            OllamaResponse with assistant's reply.

        Raises:
            OllamaUnavailableError: If Ollama is not available.
        """
        if not await self.is_available():
            raise OllamaUnavailableError("Ollama is not available")

        model_enum = model or self.config.default_model
        model_name = model_enum.value

        await self._ensure_client()
        assert self._http_client is not None

        payload: dict[str, Any] = {
            "model": model_name,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        response = await self._http_client.post(
            f"{self.config.host}/api/chat",
            json=payload,
        )

        if response.status_code != 200:
            raise OllamaUnavailableError(
                f"Ollama API error: {response.status_code} - {response.text}"
            )

        data = response.json()
        message = data.get("message", {})

        return OllamaResponse(
            content=message.get("content", ""),
            model=model_name,
            tokens_used=data.get("eval_count", 0),
            prompt_tokens=data.get("prompt_eval_count", 0),
            generation_time=data.get("total_duration", 0) / 1e9,
            is_complete=data.get("done", False),
        )

    async def embeddings(
        self,
        text: str,
        model: OllamaModel | None = None,
    ) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to generate embeddings for.
            model: Model to use (default from config).

        Returns:
            List of embedding values.

        Raises:
            OllamaUnavailableError: If Ollama is not available.
        """
        if not await self.is_available():
            raise OllamaUnavailableError("Ollama is not available")

        model_enum = model or self.config.default_model
        model_name = model_enum.value

        await self._ensure_client()
        assert self._http_client is not None

        payload = {
            "model": model_name,
            "prompt": text,
        }

        response = await self._http_client.post(
            f"{self.config.host}/api/embeddings",
            json=payload,
        )

        if response.status_code != 200:
            raise OllamaUnavailableError(
                f"Ollama API error: {response.status_code} - {response.text}"
            )

        data: dict[str, Any] = response.json()
        embedding: list[float] = data.get("embedding", [])
        return embedding

    def select_model_for_task(
        self,
        task_type: str,
        context_length_needed: int = 0,
    ) -> OllamaModel:
        """Select best model for a given task type.

        Args:
            task_type: Type of task (e.g., "analysis", "translation", "simple").
            context_length_needed: Approximate context length needed.

        Returns:
            Recommended OllamaModel for the task.
        """
        # Task-based model selection
        task_models = {
            "analysis": OllamaModel.LLAMA3_70B,
            "legal_analysis": OllamaModel.LLAMA3_70B,
            "document_review": OllamaModel.LLAMA3_70B,
            "translation": OllamaModel.MIXTRAL,
            "multilingual": OllamaModel.MIXTRAL,
            "simple": OllamaModel.PHI3,
            "quick": OllamaModel.LLAMA3_8B,
            "code": OllamaModel.CODELLAMA,
            "default": OllamaModel.LLAMA3_8B,
        }

        selected = task_models.get(task_type.lower(), OllamaModel.LLAMA3_8B)

        # Check if context length requirement changes selection
        if context_length_needed > selected.context_length:
            # Need a model with larger context
            if context_length_needed <= OllamaModel.LLAMA3_70B.context_length:
                selected = OllamaModel.LLAMA3_70B
            else:
                logger.warning(f"Requested context {context_length_needed} exceeds max available")

        return selected
