import json
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import URLError

from app.assistant.models import Message
from app.assistant.ollama_provider import OllamaProvider


class TestOllamaProvider(unittest.TestCase):

    def setUp(self):
        self.provider = OllamaProvider()
        self.messages = [
            Message(role="user", content="Hello BUTL-R!")
        ]

    @patch("app.assistant.ollama_provider.urlopen")
    def test_successful_response(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {
                "role": "assistant",
                "content": "Hello! I am BUTL-R."
            }
        }).encode("utf-8")

        mock_urlopen.return_value.__enter__.return_value = mock_response

        reply = self.provider.generate_reply(self.messages)

        self.assertEqual(reply, "Hello! I am BUTL-R.")

    @patch("app.assistant.ollama_provider.urlopen")
    def test_empty_conversation_rejected(self, mock_urlopen):
        with self.assertRaises(ValueError):
            self.provider.generate_reply([])

        mock_urlopen.assert_not_called()

    @patch("app.assistant.ollama_provider.urlopen")
    def test_connection_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Connection refused")

        with self.assertRaises(ConnectionError):
            self.provider.generate_reply(self.messages)

    @patch("app.assistant.ollama_provider.urlopen")
    def test_model_name_sent_to_ollama(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "message": {
                "role": "assistant",
                "content": "Test response"
            }
        }).encode("utf-8")

        mock_urlopen.return_value.__enter__.return_value = mock_response

        self.provider.generate_reply(self.messages)

        request = mock_urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))

        self.assertEqual(payload["model"], "gemma3:4b")
        self.assertEqual(payload["messages"][0]["content"], "Hello BUTL-R!")
        self.assertFalse(payload["stream"])


if __name__ == "__main__":
    unittest.main()