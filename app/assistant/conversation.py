
from datetime import datetime, timezone
from uuid import uuid4

from pymongo import ReturnDocument

from app.assistant.models import Message
from app.core.database import mongodb


class ConversationManager:
    """Manages conversations using MongoDB."""

    def __init__(self, database=None):
        # Use an injected database for testing,
        # otherwise use BUTL-R's main database.
        if database is None:
            database = mongodb.connect()

        self.database = database

        self.conversations = database["conversations"]
        self.messages = database["messages"]

    def create_conversation(self):
        """Create and store a new conversation."""

        conversation_id = str(uuid4())

        self.conversations.insert_one({
            "conversation_id": conversation_id,
            "created_at": datetime.now(timezone.utc),
            "message_count": 0,
        })

        return conversation_id

    def add_message(self, conversation_id, role, content):
        """Validate and store a message."""

        message = Message(
            role=role,
            content=content,
        )

        # Atomically allocate a sequence number.
        conversation = self.conversations.find_one_and_update(
            {"conversation_id": conversation_id},
            {"$inc": {"message_count": 1}},
            return_document=ReturnDocument.AFTER,
        )

        if conversation is None:
            raise KeyError("Conversation does not exist.")

        self.messages.insert_one({
            "message_id": message.message_id,
            "conversation_id": conversation_id,
            "sequence": conversation["message_count"],
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp,
        })

        return message

    def get_messages(self, conversation_id):
        """Retrieve messages in their original order."""

        conversation = self.conversations.find_one(
            {"conversation_id": conversation_id}
        )

        if conversation is None:
            raise KeyError("Conversation does not exist.")

        documents = self.messages.find(
            {"conversation_id": conversation_id}
        ).sort("sequence", 1)

        return [
            Message(
                message_id=document["message_id"],
                role=document["role"],
                content=document["content"],
                timestamp=document["timestamp"],
            )
            for document in documents
        ]

    def delete_conversation(self, conversation_id):
        """Delete a conversation and its messages."""

        conversation = self.conversations.find_one(
            {"conversation_id": conversation_id}
        )

        if conversation is None:
            raise KeyError("Conversation does not exist.")

        self.messages.delete_many({
            "conversation_id": conversation_id
        })

        self.conversations.delete_one({
            "conversation_id": conversation_id
        })
