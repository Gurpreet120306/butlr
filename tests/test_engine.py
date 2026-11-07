
import unittest
from uuid import uuid4

from pymongo import MongoClient

from app.assistant.engine import ButlrAssistant
from app.assistant.conversation import ConversationManager
from app.assistant.providers import MockAIProvider


class TestButlrAssistant(unittest.TestCase):

    def setUp(self):
        self.client = MongoClient(
            "mongodb://localhost:27017/",
            serverSelectionTimeoutMS=5000,
            tz_aware=True,
        )

        self.database_name = f"butlr_engine_test_{uuid4().hex}"
        self.database = self.client[self.database_name]

        self.manager = ConversationManager(
            database=self.database
        )

        self.assistant = ButlrAssistant(
            provider=MockAIProvider(),
            conversation_manager=self.manager,
        )

        self.conversation_id = self.assistant.start_conversation()

    def tearDown(self):
        self.client.drop_database(self.database_name)
        self.client.close()

    def test_start_conversation(self):
        self.assertIsNotNone(self.conversation_id)

    def test_send_message_returns_reply(self):
        reply = self.assistant.send_message(
            self.conversation_id,
            "Hello BUTL-R!",
        )

        self.assertIn("Hello BUTL-R!", reply)

    def test_user_and_assistant_messages_are_stored(self):
        self.assistant.send_message(
            self.conversation_id,
            "Hello!",
        )

        history = self.assistant.get_history(
            self.conversation_id
        )

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[1].role, "assistant")

    def test_multiple_messages_are_preserved(self):
        self.assistant.send_message(
            self.conversation_id,
            "My name is Alex.",
        )

        self.assistant.send_message(
            self.conversation_id,
            "What did I just tell you?",
        )

        history = self.assistant.get_history(
            self.conversation_id
        )

        self.assertEqual(len(history), 4)

    def test_conversation_deletion(self):
        self.assistant.delete_conversation(
            self.conversation_id
        )

        with self.assertRaises(KeyError):
            self.assistant.get_history(self.conversation_id)


if __name__ == "__main__":
    unittest.main()
