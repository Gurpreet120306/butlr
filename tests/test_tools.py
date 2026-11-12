import unittest
from pathlib import Path
from mongomock import MongoClient

from app.tools.apps import ApplicationManager
from app.tools.files import SafeFileManager
from app.tools.notifications import NotificationManager
from app.tools.settings import UserPreferences
from app.security.policy import SecurityPolicy
from app.security.audit import AuditLogger


class TestDesktopTools(unittest.TestCase):

    def setUp(self):
        self.client = MongoClient()
        self.database = self.client["butlr_tools_test"]
        self.audit_logger = AuditLogger(database=self.database)
        self.policy = SecurityPolicy()

    def tearDown(self):
        self.client.close()

    def test_application_manager_rejects_unapproved_apps(self):
        """Unapproved applications are blocked by default-deny rule."""
        app_mgr = ApplicationManager(security_policy=self.policy, audit_logger=self.audit_logger)
        success, msg = app_mgr.launch("malicious_tool.exe")

        self.assertFalse(success)
        self.assertIn("approved whitelist", msg)

    def test_application_manager_approved_list(self):
        """Approved apps list contains safe system utilities."""
        app_mgr = ApplicationManager(security_policy=self.policy)
        apps = app_mgr.get_approved_applications()

        self.assertIn("notepad", apps)
        self.assertIn("calculator", apps)

    def test_file_manager_path_traversal_defense(self):
        """FileManager prevents accessing files outside approved roots."""
        temp_root = Path(__file__).resolve().parent
        file_mgr = SafeFileManager(allowed_roots=[temp_root])

        # Attempt path traversal to Windows directory
        success, msg = file_mgr.read_text_file(r"C:\Windows\System32\drivers\etc\hosts")
        self.assertFalse(success)
        self.assertIn("outside approved directories", msg)

    def test_file_manager_read_existing_file(self):
        """FileManager reads existing files within allowed root."""
        test_file = Path(__file__).resolve()
        file_mgr = SafeFileManager(allowed_roots=[test_file.parent])

        success, content = file_mgr.read_text_file(str(test_file))
        self.assertTrue(success)
        self.assertIn("TestDesktopTools", content)

    def test_notifications_manager_records_notification(self):
        """NotificationManager saves notifications to database."""
        notifier = NotificationManager(database=self.database)
        record = notifier.notify("Meeting Reminder", "Team sync at 10 AM", show_desktop=False)

        self.assertEqual(record["title"], "Meeting Reminder")
        logs = notifier.get_notifications()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["title"], "Meeting Reminder")

    def test_user_preferences_persistence(self):
        """UserPreferences saves and retrieves custom settings."""
        prefs = UserPreferences(database=self.database)
        self.assertEqual(prefs.get_setting("user_name"), "Sir")

        prefs.set_setting("user_name", "Gurpreet")
        self.assertEqual(prefs.get_setting("user_name"), "Gurpreet")

        prefs.set_setting("voice_rate", 2)
        all_settings = prefs.get_all_settings()
        self.assertEqual(all_settings["user_name"], "Gurpreet")
        self.assertEqual(all_settings["voice_rate"], 2)


if __name__ == "__main__":
    unittest.main()
