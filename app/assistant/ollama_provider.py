import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.assistant.models import Message
from app.assistant.providers import BaseAIProvider


class OllamaProvider(BaseAIProvider):
    """Connects BUTL-R to a locally running Ollama model."""

    def __init__(
        self,
        model: str = "gemma3:4b",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate_reply(self, messages: list[Message]) -> str:
        if not messages:
            raise ValueError("Conversation cannot be empty.")

        ollama_messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
        }

        request = Request(
            url=f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))

            reply = result.get("message", {}).get("content", "")

            if not reply.strip():
                raise RuntimeError("Ollama returned an empty response.")

            return reply.strip()

        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Ollama API error ({error.code}): {details}"
            ) from error

        except URLError as error:
            raise ConnectionError(
                "Could not connect to Ollama. "
                "Make sure Ollama is running."
            ) from error

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Ollama returned an invalid JSON response."
            ) from error
        