
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.assistant.models import Message
from app.assistant.providers import BaseAIProvider



BUTLR_SYSTEM_PROMPT = """
You are BUTL-R, a personal AI assistant.

ABOUT THE USER'S PROJECT:
- The user is building a personal AI assistant called BUTL-R.
- This project is written in Python.
- It uses MongoDB for conversation storage.
- It uses Ollama for local AI models.
- It currently supports Gemma 3 1B and Gemma 3 4B.
- The project is being developed on Windows 11.
- The long-term goal is to build a capable personal AI assistant
  with voice interaction, memory, and desktop integration.

Your purpose is to help the user with everyday questions,
learning, programming, planning, and problem-solving.

PERSONALITY:
- Be friendly, natural, respectful, and helpful.
- Speak clearly and avoid unnecessarily complicated language.
- Be conversational rather than overly formal.
- Give detailed explanations when requested.
- Keep simple answers short.

CONVERSATION RULES:
- Respond positively to ordinary greetings.
- Use the available conversation history.
- Never invent the user's name, projects, or personal details.
- If you don't know something, say so honestly.
- Do not make up fictional information to fill gaps.
- Do not claim to have performed actions you haven't performed.
- Never treat harmless greetings as abusive or dangerous.

IDENTITY:
- Your name is BUTL-R.
- You are the user's personal AI assistant.
- You are running locally through Ollama.
"""


class OllamaProvider(BaseAIProvider):
    """Connects BUTL-R to a locally running Ollama model."""

    AVAILABLE_MODES = {
        "fast": "gemma3:1b",
        "quality": "gemma3:4b",
    }

    def __init__(
        self,
        model: str = "gemma3:4b",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Identify the current mode from the selected model.
        self.mode = next(
            (
                mode
                for mode, model_name in self.AVAILABLE_MODES.items()
                if model_name == model
            ),
            "custom",
        )

    def set_mode(self, mode: str):
        """Switch between Fast Mode and Quality Mode."""

        mode = mode.lower().strip()

        if mode not in self.AVAILABLE_MODES:
            raise ValueError(
                "Invalid mode. Choose 'fast' or 'quality'."
            )

        self.mode = mode
        self.model = self.AVAILABLE_MODES[mode]

        return self.model

    def generate_reply(self, messages: list[Message]) -> str:
        if not messages:
            raise ValueError("Conversation cannot be empty.")
        ollama_messages = [
       {
            "role": "system",
            "content": BUTLR_SYSTEM_PROMPT,
        }
    ] + [
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
            "keep_alive": "30m",
        }

        request = Request(
            url=f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(
                    response.read().decode("utf-8")
                )

            reply = result.get("message", {}).get("content", "")

            if not reply.strip():
                raise RuntimeError(
                    "Ollama returned an empty response."
                )

            return reply.strip()

        except HTTPError as error:
            details = error.read().decode(
                "utf-8",
                errors="replace",
            )

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
