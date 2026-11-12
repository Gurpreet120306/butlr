import json
import unittest
from unittest.mock import patch, MagicMock
from mongomock import MongoClient

from app.tools.web import WebSearchAssistant
from app.security.privacy import PrivacyManager
from app.security.policy import SecurityPolicy


class TestWebResearch(unittest.TestCase):

    def setUp(self):
        self.client = MongoClient()
        self.database = self.client["butlr_web_test"]
        self.privacy_mgr = PrivacyManager(database=self.database)
        self.policy = SecurityPolicy()

    def tearDown(self):
        self.client.close()

    def test_search_blocked_in_local_only_mode(self):
        """Web search must be strictly blocked when local-only mode is active."""
        assistant = WebSearchAssistant(
            privacy_manager=self.privacy_mgr,
            security_policy=self.policy,
        )

        success, msg = assistant.search("Python programming")
        self.assertFalse(success)
        self.assertIn("Local-Only Mode", msg)

    def test_search_requires_confirmation_when_network_enabled(self):
        """When network is enabled, sensitive outbound request requires confirmation."""
        self.privacy_mgr.set_cloud_allowed(True)
        assistant = WebSearchAssistant(
            privacy_manager=self.privacy_mgr,
            security_policy=self.policy,
        )

        success, msg = assistant.search("Python programming", user_confirmed=False)
        self.assertFalse(success)
        self.assertIn("Confirmation required", msg)

    @patch("urllib.request.urlopen")
    def test_search_successful_when_confirmed(self, mock_urlopen):
        """Authorized and confirmed web query retrieves and sanitizes content."""
        self.privacy_mgr.set_cloud_allowed(True)
        assistant = WebSearchAssistant(
            privacy_manager=self.privacy_mgr,
            security_policy=self.policy,
        )

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "AbstractText": "Python is a high-level, general-purpose programming language."
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        success, result = assistant.search("Python programming", user_confirmed=True)
        self.assertTrue(success)
        self.assertIn("Python is a high-level", result)


if __name__ == "__main__":
    unittest.main()
