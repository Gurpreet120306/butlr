from datetime import datetime, timezone
from typing import Any, Optional

from app.core.database import mongodb


class PrivacyManager:
    """Manages user privacy settings, local-only enforcement, and data retention."""

    def __init__(self, database=None, local_only: bool = True):
        if database is None:
            database = mongodb.connect()

        self.database = database
        self.settings_collection = database["user_settings"]
        self.conversations = database["conversations"]
        self.messages = database["messages"]
        self.memories = database["memories"]

        # Default privacy guarantees
        self.local_only = local_only
        self.telemetry_enabled = False
        self.microphone_enabled = False  # Explicit privacy mute by default

    def is_cloud_allowed(self) -> bool:
        """Check if cloud transmission is permitted."""
        return not self.local_only

    def set_cloud_allowed(self, allowed: bool) -> None:
        """Explicitly enable or disable cloud AI connections."""
        self.local_only = not allowed

    def set_microphone_enabled(self, enabled: bool) -> None:
        """Toggle microphone access state."""
        self.microphone_enabled = enabled

    def export_user_data(self) -> dict[str, Any]:
        """Export all conversations and persistent memories in standard JSON-serializable format."""
        all_conversations = list(
            self.conversations.find({}, {"_id": 0})
        )
        all_messages = list(
            self.messages.find({}, {"_id": 0})
        )
        all_memories = list(
            self.memories.find({}, {"_id": 0})
        )

        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "privacy_mode": "local_only" if self.local_only else "cloud_enabled",
            "conversations_count": len(all_conversations),
            "messages_count": len(all_messages),
            "memories_count": len(all_memories),
            "conversations": all_conversations,
            "messages": all_messages,
            "memories": all_memories,
        }

    def purge_all_conversations(self) -> int:
        """Permanently delete all conversations and message history."""
        deleted_msgs = self.messages.delete_many({}).deleted_count
        self.conversations.delete_many({})
        return deleted_msgs

    def purge_all_memories(self) -> int:
        """Permanently delete all persistent long-term memories."""
        return self.memories.delete_many({}).deleted_count
