
from uuid import uuid4

from app.assistant.models import Message


class ConversationManager:
    """Manages separate conversations and their messages."""

    def __init__(self):
        self._conversations = {}

    def create_conversation(self):
        """Create and return a new conversation ID."""

        conversation_id = str(uuid4())

        self._conversations[conversation_id] = []

        return conversation_id

    def add_message(self, conversation_id, role, content):
        """Add a message to an existing conversation."""

        if conversation_id not in self._conversations:
            raise KeyError("Conversation does not exist.")

        message = Message(
            role=role,
            content=content
        )

        self._conversations[conversation_id].append(message)

        return message

    def get_messages(self, conversation_id):
        """Return the messages in a conversation."""

        if conversation_id not in self._conversations:
            raise KeyError("Conversation does not exist.")

        return list(self._conversations[conversation_id])

    def delete_conversation(self, conversation_id):
        """Delete a conversation."""

        if conversation_id not in self._conversations:
            raise KeyError("Conversation does not exist.")

        del self._conversations[conversation_id]
