
import unittest
from uuid import uuid4

from pymongo import MongoClient

from app.assistant.models import Message
from app.assistant.conversation import ConversationManager


class TestConversationManager(unittest.TestCase):

    def setUp(self):
        # Give every test its own temporary database.
        self.client = MongoClient(
            "mongodb://localhost:27017/",
            serverSelectionTimeoutMS=5000,
            tz_aware=True,
        )

        self.database_name = f"butlr_test_{uuid4().hex}"

        self.database = self.client[self.database_name]

        self.manager = ConversationManager(
            database=self.database
        )

        self.conversation_id = (
            self.manager.create_conversation()
        )

    def tearDown(self):
        # Delete only this test's database.
        self.client.drop_database(self.database_name)
        self.client.close()

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

        restarted_manager = ConversationManager(
            database=self.database
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

        remaining = self.database.messages.count_documents(
            {"conversation_id": self.conversation_id}
        )

        self.assertEqual(remaining, 0)

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
            database=self.database
        )

        messages = restarted_manager.get_messages(
            self.conversation_id
        )

        self.assertEqual(len(messages), 2)
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
