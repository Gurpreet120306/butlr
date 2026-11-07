from app.assistant.conversation import ConversationManager
from app.assistant.providers import BaseAIProvider


class ButlrAssistant:
    """Connects conversation management with an AI provider."""

    def __init__(self, provider: BaseAIProvider):
        self.provider = provider
        self.conversation_manager = ConversationManager()

    def start_conversation(self):
        """Start a new conversation."""
        return self.conversation_manager.create_conversation()

    def send_message(self, conversation_id: str, content: str) -> str:
        """Send a message and receive an AI response."""

        # Store the user's message.
        self.conversation_manager.add_message(
            conversation_id,
            "user",
            content,
        )

        # Retrieve the complete conversation history.
        messages = self.conversation_manager.get_messages(
            conversation_id
        )

        # Ask the configured AI provider to generate a reply.
        reply = self.provider.generate_reply(messages)

        # Store the AI's response.
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