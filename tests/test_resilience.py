import unittest
from unittest.mock import MagicMock
from mongomock import MongoClient

from app.assistant.engine import ButlrAssistant
from app.assistant.conversation import ConversationManager
from app.assistant.memory import MemoryManager
from app.core.resilience import retry_with_backoff, FallbackHandler
from app.core.database import MongoDB
from app.security.policy import SecurityPolicy
from app.security.audit import AuditLogger


class TestResilienceAndRecovery(unittest.TestCase):

    def setUp(self):
        self.client = MongoClient()
        self.database = self.client["butlr_resilience_test"]

    def tearDown(self):
        self.client.close()

    def test_retry_with_backoff_success_after_failure(self):
        """Should retry on transient exception and return result once successful."""
        attempts = 0

        def flaky_service():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionResetError("Transient network glitch")
            return "SUCCESS"

        result = retry_with_backoff(
            flaky_service,
            max_retries=3,
            initial_delay=0.01,
            backoff_factor=1.5,
            exceptions=(ConnectionResetError,),
        )

        self.assertEqual(result, "SUCCESS")
        self.assertEqual(attempts, 3)

    def test_retry_with_backoff_exhaustion(self):
        """Should raise after max_retries attempts fail."""
        def broken_service():
            raise ConnectionRefusedError("Offline")

        with self.assertRaises(ConnectionRefusedError):
            retry_with_backoff(
                broken_service,
                max_retries=2,
                initial_delay=0.01,
                exceptions=(ConnectionRefusedError,),
            )

    def test_fallback_handler_messages(self):
        """FallbackHandler must return helpful messages for different error types."""
        conn_msg = FallbackHandler.get_fallback(ConnectionError("Refused"))
        self.assertIn("Ollama", conn_msg)

        timeout_msg = FallbackHandler.get_fallback(TimeoutError("Timed out"))
        self.assertIn("Fast Mode", timeout_msg)

        generic_msg = FallbackHandler.get_fallback(ValueError("Bad value"))
        self.assertIn("unexpected issue", generic_msg)

    def test_engine_gracefully_handles_ai_provider_failure(self):
        """When AI provider fails, engine returns polite fallback without crashing."""
        failing_provider = MagicMock()
        failing_provider.generate_reply.side_effect = ConnectionError("Ollama is down")

        assistant = ButlrAssistant(
            provider=failing_provider,
            conversation_manager=ConversationManager(database=self.database),
            memory_manager=MemoryManager(database=self.database),
            security_policy=SecurityPolicy(),
            audit_logger=AuditLogger(database=self.database),
        )
        cid = assistant.start_conversation()

        reply = assistant.send_message(cid, "Hello BUTL-R")

        self.assertIn("Ollama", reply)
        # Verify history preserved both messages
        history = assistant.get_history(cid)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].role, "user")
        self.assertEqual(history[1].role, "assistant")


if __name__ == "__main__":
    unittest.main()
