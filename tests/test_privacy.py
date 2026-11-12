import unittest
from mongomock import MongoClient

from app.assistant.engine import ButlrAssistant
from app.assistant.conversation import ConversationManager
from app.assistant.memory import MemoryManager
from app.assistant.providers import MockAIProvider
from app.security.privacy import PrivacyManager
from app.security.policy import SecurityPolicy
from app.security.audit import AuditLogger


class TestPrivacyManager(unittest.TestCase):

    def setUp(self):
        self.client = MongoClient()
        self.database = self.client["butlr_privacy_test"]
        self.privacy_manager = PrivacyManager(database=self.database)

    def tearDown(self):
        self.client.close()

    def test_default_local_only(self):
        """BUTL-R must operate locally by default; cloud transmission is disabled."""
        self.assertTrue(self.privacy_manager.local_only)
        self.assertFalse(self.privacy_manager.is_cloud_allowed())
        self.assertFalse(self.privacy_manager.telemetry_enabled)
        self.assertFalse(self.privacy_manager.microphone_enabled)

    def test_toggle_cloud_allowed(self):
        """User can explicitly grant or revoke cloud connectivity."""
        self.privacy_manager.set_cloud_allowed(True)
        self.assertTrue(self.privacy_manager.is_cloud_allowed())

        self.privacy_manager.set_cloud_allowed(False)
        self.assertFalse(self.privacy_manager.is_cloud_allowed())

    def test_microphone_toggle(self):
        """Microphone state can be toggled and defaults to disabled."""
        self.privacy_manager.set_microphone_enabled(True)
        self.assertTrue(self.privacy_manager.microphone_enabled)

        self.privacy_manager.set_microphone_enabled(False)
        self.assertFalse(self.privacy_manager.microphone_enabled)

    def test_export_and_purge_user_data(self):
        """Export user data to portable JSON format, then verify purge."""
        conv_mgr = ConversationManager(database=self.database)
        mem_mgr = MemoryManager(database=self.database)

        cid = conv_mgr.create_conversation()
        conv_mgr.add_message(cid, "user", "Sensitive discussion")
        mem_mgr.save_memory("profile", "city", "Delhi")

        # Export
        data = self.privacy_manager.export_user_data()
        self.assertEqual(data["conversations_count"], 1)
        self.assertEqual(data["messages_count"], 1)
        self.assertEqual(data["memories_count"], 1)
        self.assertEqual(data["memories"][0]["key"], "city")

        # Purge conversations
        self.privacy_manager.purge_all_conversations()
        self.assertEqual(self.database["conversations"].count_documents({}), 0)
        self.assertEqual(self.database["messages"].count_documents({}), 0)
        self.assertEqual(self.database["memories"].count_documents({}), 1)

        # Purge memories
        self.privacy_manager.purge_all_memories()
        self.assertEqual(self.database["memories"].count_documents({}), 0)

    def test_engine_privacy_integration(self):
        """Engine exposes privacy export and purge with audit logging."""
        audit_logger = AuditLogger(database=self.database)
        assistant = ButlrAssistant(
            provider=MockAIProvider(),
            conversation_manager=ConversationManager(database=self.database),
            memory_manager=MemoryManager(database=self.database),
            security_policy=SecurityPolicy(),
            audit_logger=audit_logger,
            privacy_manager=self.privacy_manager,
        )

        assistant.remember("test", "fav_color", "blue")
        self.assertEqual(assistant.recall("test", "fav_color"), "blue")

        # Purge through engine
        assistant.purge_all_memories()
        self.assertIsNone(assistant.recall("test", "fav_color"))

        # Verify audit log recorded the privacy event
        logs = audit_logger.get_recent_logs(limit=10)
        self.assertTrue(any(log["event_type"] == "privacy_purge" for log in logs))


if __name__ == "__main__":
    unittest.main()
