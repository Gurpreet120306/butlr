
from app.assistant.conversation import ConversationManager
from app.assistant.providers import BaseAIProvider


class ButlrAssistant:
    """Connects conversation management with an AI provider."""

    def __init__(
        self,
        provider: BaseAIProvider,
        conversation_manager=None,
    ):
        self.provider = provider

        self.conversation_manager = (
            conversation_manager
            if conversation_manager is not None
            else ConversationManager()
        )

    def start_conversation(self):
        """Start a new conversation."""
        return self.conversation_manager.create_conversation()

    def set_mode(self, mode: str):
        """Switch between supported AI modes."""

        if not hasattr(self.provider, "set_mode"):
            raise RuntimeError(
                "The configured AI provider does not support mode switching."
            )

        return self.provider.set_mode(mode)

    def get_mode(self):
        """Return the current AI mode."""

        return getattr(self.provider, "mode", "unknown")

    def send_message(self, conversation_id: str, content: str) -> str:
        """Send a message and receive an AI response."""

        self.conversation_manager.add_message(
            conversation_id,
            "user",
            content,
        )

        messages = self.conversation_manager.get_messages(
            conversation_id
        )

        reply = self.provider.generate_reply(messages)

        self.conversation_manager.add_message(
            conversation_id,
            "assistant",
            reply,
        )

        return reply

    def get_history(self, conversation_id: str):
        """Retrieve all messages in a conversation."""
        return self.conversation_manager.get_messages(conversation_id)

    def delete_conversation(self, conversation_id: str):
        """Delete a conversation."""
        self.conversation_manager.delete_conversation(conversation_id)
