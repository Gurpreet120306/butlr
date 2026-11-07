
import unittest

from app.assistant.models import Message
from app.assistant.conversation import ConversationManager


class TestConversationManager(unittest.TestCase):

    def setUp(self):
        self.manager = ConversationManager()
        self.conversation_id = self.manager.create_conversation()

    def test_create_conversation(self):
        self.assertIsNotNone(self.conversation_id)

    def test_add_user_message(self):
        message = self.manager.add_message(
            self.conversation_id,
            "user",
            "Hello BUTL-R!"
        )

        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello BUTL-R!")

    def test_retrieve_messages(self):
        self.manager.add_message(
            self.conversation_id,
            "user",
            "Hello"
        )

        messages = self.manager.get_messages(self.conversation_id)

        self.assertEqual(len(messages), 1)

    def test_conversations_are_separate(self):
        second_id = self.manager.create_conversation()

        self.manager.add_message(
            self.conversation_id,
            "user",
            "First conversation"
        )

        self.assertEqual(
            len(self.manager.get_messages(second_id)),
            0
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


if __name__ == "__main__":
    unittest.main()

