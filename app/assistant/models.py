
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class Message:
    """Represents one message in a conversation."""

    role: str
    content: str

    message_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        allowed_roles = {"system", "user", "assistant"}

        if self.role not in allowed_roles:
            raise ValueError(
                f"Invalid message role: {self.role}"
            )

        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("Message content cannot be empty.")
    