
from datetime import datetime, timezone

from app.core.database import mongodb


SENSITIVE_KEYWORDS = (
    "password",
    "passwd",
    "passcode",
    "pin",
    "api key",
    "secret",
    "access token",
    "refresh token",
    "private key",
    "recovery phrase",
    "seed phrase",
    "credit card",
    "cvv",
    "bank account",
)


class MemoryManager:
    """Manages BUTL-R's long-term memories using MongoDB."""

    def __init__(self, database=None):
        # Use an injected database for testing,
        # otherwise connect to BUTL-R's MongoDB database.
        if database is None:
            database = mongodb.connect()

        self.database = database
        self.memories = database["memories"]


    def _validate_memory(self, category, key, value):
        """Validate memory data and reject obvious secrets."""

        if not all(
            isinstance(item, str) and item.strip()
            for item in (category, key, value)
        ):
            raise ValueError(
                "Category, key, and value must be non-empty strings."
            )

        combined_text = f"{category} {key} {value}".lower()

        for keyword in SENSITIVE_KEYWORDS:
            if keyword in combined_text:
                raise ValueError(
                    "This information appears sensitive "
                    "and cannot be saved in BUTL-R memory."
                )


    def save_memory(self, category, key, value):
        """Save a new memory or update an existing one."""

        self._validate_memory(category, key, value)

        now = datetime.now(timezone.utc)

        self.memories.update_one(
            {
                "category": category.strip().lower(),
                "key": key.strip().lower(),
            },
            {
                "$set": {
                    "value": value.strip(),
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )

        return True

    def get_memory(self, category, key):
        """Retrieve a specific memory."""

        if not isinstance(category, str) or not category.strip():
            raise ValueError("Category cannot be empty.")

        if not isinstance(key, str) or not key.strip():
            raise ValueError("Key cannot be empty.")

        memory = self.memories.find_one({
            "category": category.strip().lower(),
            "key": key.strip().lower(),
        })

        if memory is None:
            return None

        return memory["value"]

    def delete_memory(self, category, key):
        """Delete a specific memory."""

        if not isinstance(category, str) or not category.strip():
            raise ValueError("Category cannot be empty.")

        if not isinstance(key, str) or not key.strip():
            raise ValueError("Key cannot be empty.")

        result = self.memories.delete_one({
            "category": category.strip().lower(),
            "key": key.strip().lower(),
        })

        return result.deleted_count > 0
