from datetime import datetime, timezone
import hashlib
import json
from typing import Any


class SyncPayloadManager:
    """Handles packaging and verifying synchronization payloads for companion devices."""

    def __init__(self, device_name: str = "BUTL-R Host"):
        self.device_name = device_name

    def create_sync_payload(self, conversations: list[dict], user_settings: dict) -> dict[str, Any]:
        """Bundle sanitized state for cross-device sync."""
        timestamp = datetime.now(timezone.utc).isoformat()
        body = {
            "source_device": self.device_name,
            "timestamp": timestamp,
            "conversations": conversations,
            "settings": user_settings,
        }
        # Generate SHA256 checksum for payload integrity verification
        serialized = json.dumps(body, sort_keys=True, default=str)
        checksum = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return {
            "payload": body,
            "checksum": checksum,
        }

    def verify_sync_payload(self, sync_data: dict[str, Any]) -> bool:
        """Verify the integrity checksum of an incoming sync payload."""
        payload = sync_data.get("payload")
        checksum = sync_data.get("checksum")
        if not payload or not checksum:
            return False

        serialized = json.dumps(payload, sort_keys=True, default=str)
        expected = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return checksum == expected
