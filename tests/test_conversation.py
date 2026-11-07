import unittest
import tempfile

from pathlib import Path

from app.assistant.models import Message
from app.assistant.conversation import ConversationManager


class TestConversationManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.db_path = Path(self.temp_dir.name) / "test.db"

        self.manager = ConversationManager(
            db_path=self.db_path
        )

        self.conversation_id = self.manager.create_conversation()

    def test_create_conversation(self):
        self.assertIsNotNone(self.conversation_id)

    def test_add_user_message(self):
        message = self.manager.add_message(
            self.conversation_id,
            "user",
            "Hello BUTL-R!",
        )

        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello BUTL-R!")

    def test_retrieve_messages(self):
        self.manager.add_message(
            self.conversation_id,
            "user",
            "Hello",
        )

        messages = self.manager.get_messages(
            self.conversation_id
        )

        self.assertEqual(len(messages), 1)

    def test_conversations_are_separate(self):
        second_id = self.manager.create_conversation()

        self.manager.add_message(
            self.conversation_id,
            "user",
            "First conversation",
        )

        self.assertEqual(
            len(self.manager.get_messages(second_id)),
            0,
        )

    def test_invalid_message_role(self):
        with self.assertRaises(ValueError):
            Message(role="admin", content="Invalid")

    def test_empty_message_rejected(self):
        with self.assertRaises(ValueError):
            Message(role="user", content=" ")

    def test_unknown_conversation_rejected(self):
        with self.assertRaises(KeyError):
            self.manager.get_messages("unknown-id")

    def test_conversation_survives_restart(self):

        self.manager.add_message(
            self.conversation_id,
            "user",
            "My name is Gurpreet.",
        )

        # Simulate restarting BUTL-R by creating
        # another manager using the same database.
        restarted_manager = ConversationManager(
            db_path=self.db_path
        )

        messages = restarted_manager.get_messages(
            self.conversation_id
        )

        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0].content,
            "My name is Gurpreet.",
        )

    def test_delete_conversation_removes_messages(self):

        self.manager.add_message(
            self.conversation_id,
            "user",
            "This message should be deleted.",
        )

        self.manager.delete_conversation(
            self.conversation_id
        )

        with self.assertRaises(KeyError):
            self.manager.get_messages(
                self.conversation_id
            )

    def test_message_order_survives_restart(self):

        self.manager.add_message(
            self.conversation_id,
            "user",
            "First message",
        )

        self.manager.add_message(
            self.conversation_id,
            "assistant",
            "Second message",
        )

        restarted_manager = ConversationManager(
            db_path=self.db_path
        )

        messages = restarted_manager.get_messages(
            self.conversation_id
        )

        self.assertEqual(
            messages[0].content,
            "First message",
        )

        self.assertEqual(
            messages[1].content,
            "Second message",
        )

if __name__ == "__main__":
    unittest.main()