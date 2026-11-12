from typing import Any
from app.core.database import mongodb


class UserPreferences:
    """Manages persistent user preferences, voice parameters, and behavior customization."""

    DEFAULT_SETTINGS = {
        "user_name": "Sir",
        "preferred_mode": "fast",
        "voice_enabled": True,
        "voice_rate": 1,
        "voice_volume": 100,
        "theme": "dark",
        "auto_speak_responses": True,
    }

    def __init__(self, database=None):
        if database is None:
            database = mongodb.connect()
        self.database = database
        self.settings_collection = database["user_settings"]

    def get_setting(self, key: str) -> Any:
        """Retrieve a specific user preference."""
        doc = self.settings_collection.find_one({"key": key})
        if doc and "value" in doc:
            return doc["value"]
        return self.DEFAULT_SETTINGS.get(key)

    def set_setting(self, key: str, value: Any) -> None:
        """Save or update a specific user preference."""
        self.settings_collection.update_one(
            {"key": key},
            {"$set": {"value": value}},
            upsert=True,
        )

    def get_all_settings(self) -> dict[str, Any]:
        """Return all user settings merged with system defaults."""
        settings = dict(self.DEFAULT_SETTINGS)
        for doc in self.settings_collection.find({}):
            if "key" in doc and "value" in doc:
                settings[doc["key"]] = doc["value"]
        return settings
