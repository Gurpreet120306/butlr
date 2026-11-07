import unittest

from app.assistant.models import Message
from app.assistant.providers import (
    BaseAIProvider,
    MockAIProvider,
)


class TestAIProviders(unittest.TestCase):

    def setUp(self):
        self.provider = MockAIProvider()

    def test_mock_provider_uses_base_interface(self):
        self.assertIsInstance(
            self.provider,
            BaseAIProvider
        )

    def test_empty_conversation(self):
        reply = self.provider.generate_reply([])
        self.assertIn("BUTL-R", reply)

    def test_user_message_response(self):
        messages = [
            Message(role="user", content="Hello BUTL-R")
        ]

        reply = self.provider.generate_reply(messages)

        self.assertIn("Hello BUTL-R", reply)
        self.assertIn("received your message", reply)

    def test_non_user_last_message(self):
        messages = [
            Message(role="assistant", content="Previous reply")
        ]

        reply = self.provider.generate_reply(messages)

        self.assertIn("send me a message", reply)


if __name__ == "__main__":
    unittest.main()