import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.database import mongodb
from app.security.sanitizer import sanitize_parameters


class AuditLogger:
    """Maintains an append-only, tamper-evident audit log for security events."""

    def __init__(self, database=None):
        if database is None:
            database = mongodb.connect()

        self.database = database
        self.audit_collection = database["audit_logs"]
        self.logger = logging.getLogger("BUTL-R.Security")

    def log_event(
        self,
        event_type: str,
        action_type: str,
        decision: str,
        reason: str,
        requested_by: str = "ai",
        conversation_id: str = "",
        target: str = "",
        parameters: Optional[dict[str, Any]] = None,
    ) -> dict:
        """Record a security decision or policy event."""
        sanitized_params = sanitize_parameters(parameters or {})
        now = datetime.now(timezone.utc)

        log_entry = {
            "timestamp": now,
            "event_type": event_type,
            "action_type": action_type,
            "decision": decision,
            "reason": reason,
            "requested_by": requested_by,
            "conversation_id": conversation_id,
            "target": target,
            "parameters": sanitized_params,
        }

        self.audit_collection.insert_one(log_entry)

        # Mirror to Python logging
        log_msg = (
            f"SECURITY AUDIT | event={event_type} | action={action_type} | "
            f"decision={decision} | target={target} | reason={reason}"
        )
        if decision == "denied":
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)

        return log_entry

    def get_recent_logs(self, limit: int = 50) -> list[dict]:
        """Retrieve recent security audit entries in reverse chronological order."""
        return list(
            self.audit_collection.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )

    def get_logs_by_action(self, action_type: str) -> list[dict]:
        """Retrieve all audit records for a specific action."""
        return list(
            self.audit_collection.find(
                {"action_type": action_type},
                {"_id": 0},
            ).sort("timestamp", -1)
        )
