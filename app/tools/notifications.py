import logging
import subprocess
from datetime import datetime, timezone
from typing import Optional

from app.core.database import mongodb

logger = logging.getLogger("BUTL-R.Tools.Notifications")


class NotificationManager:
    """Delivers user reminders, desktop notifications, and alerts."""

    def __init__(self, database=None):
        if database is None:
            database = mongodb.connect()
        self.database = database
        self.notifications_collection = database["notifications"]

    def notify(self, title: str, message: str, show_desktop: bool = True) -> dict:
        """Deliver and log a notification alert."""
        now = datetime.now(timezone.utc)
        record = {
            "title": title,
            "message": message,
            "timestamp": now,
            "delivered": False,
        }

        if show_desktop:
            # Deliver Windows desktop notification
            clean_title = title.replace("'", "''").replace('"', '`"')
            clean_msg = message.replace("'", "''").replace('"', '`"')
            ps_script = (
                f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
                f"$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
                f"$textNodes = $template.GetElementsByTagName('text'); "
                f"$textNodes.Item(0).AppendChild($template.CreateTextNode('{clean_title}')) > $null; "
                f"$textNodes.Item(1).AppendChild($template.CreateTextNode('{clean_msg}')) > $null; "
                f"$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
                f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('BUTL-R').Show($toast);"
            )
            try:
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-Command", ps_script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                record["delivered"] = True
            except Exception as err:
                logger.warning(f"Could not display native desktop toast: {err}")

        self.notifications_collection.insert_one(record)
        return record

    def get_notifications(self, limit: int = 20) -> list[dict]:
        """Retrieve recent notifications."""
        return list(
            self.notifications_collection.find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
