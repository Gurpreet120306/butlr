import unittest

from app.assistant.engine import ButlrAssistant
from app.assistant.providers import MockAIProvider


class TestButlrAssistant(unittest.TestCase):

    def setUp(self):
        self.assistant = ButlrAssistant(
            provider=MockAIProvider()
        )
        self.conversation_id = self.assistant.start_conversation()

    def test_start_conversation(self):
        self.assertIsNotNone(self.conversation_id)

    def test_send_message_returns_reply(self):
        reply = self.assistant.send_message(
            self.conversation_id,
            "Hello BUTL-R!"
        )

        self.assertIn("Hello BUTL-R!", reply)

    def test_user_and_assistant_messages_are_stored(self):
        self.assistant.send_message(
            self.conversation_id,
            "Hello!"
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
            "My name is Alex."
        )

        self.assistant.send_message(
            self.conversation_id,
            "What did I just tell you?"
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