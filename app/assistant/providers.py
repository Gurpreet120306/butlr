from abc import ABC, abstractmethod

from app.assistant.models import Message


class BaseAIProvider(ABC):
    """Common interface for all BUTL-R AI providers."""

    @abstractmethod
    def generate_reply(self, messages: list[Message]) -> str:
        """Generate a response using the conversation history."""
        pass


class MockAIProvider(BaseAIProvider):
    """Temporary AI provider used for testing."""

    def generate_reply(self, messages: list[Message]) -> str:
        if not messages:
            return "Hello! I am BUTL-R. How can I help you?"

        last_message = messages[-1]

        if last_message.role != "user":
            return "Please send me a message first."

        return (
            f"Hello! I received your message: "
            f"'{last_message.content}'. "
            f"My AI connection is not configured yet."
        )