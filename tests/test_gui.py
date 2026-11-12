import os
import unittest
from unittest.mock import MagicMock
from mongomock import MongoClient

# Run Qt headless for CI/test environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from app.assistant.engine import ButlrAssistant
from app.assistant.conversation import ConversationManager
from app.assistant.memory import MemoryManager
from app.assistant.providers import MockAIProvider
from app.gui.main_window import ButlrMainWindow
from app.gui.worker import AssistantWorker
from app.security.policy import SecurityPolicy
from app.security.audit import AuditLogger
from app.security.privacy import PrivacyManager


class TestDesktopGUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])

    def setUp(self):
        self.client = MongoClient()
        self.database = self.client["butlr_gui_test"]
        self.assistant = ButlrAssistant(
            provider=MockAIProvider(),
            conversation_manager=ConversationManager(database=self.database),
            memory_manager=MemoryManager(database=self.database),
            security_policy=SecurityPolicy(),
            audit_logger=AuditLogger(database=self.database),
            privacy_manager=PrivacyManager(database=self.database),
        )
        self.window = ButlrMainWindow(self.assistant)

    def tearDown(self):
        self.window.close()
        self.client.close()

    def test_main_window_initialization(self):
        """Main window initializes with correct title, central widget, and status label."""
        self.assertIn("BUTL-R", self.window.windowTitle())
        self.assertIsNotNone(self.window.centralWidget())
        self.assertIn("MongoDB", self.window.top_status_label.text())

    def test_append_message(self):
        """Messages appear in the chat display."""
        self.window._append_message("You", "Hello GUI", is_user=True)
        html_content = self.window.chat_display.toHtml()
        self.assertIn("Hello GUI", html_content)
        self.assertIn("You", html_content)

    def test_worker_thread_execution(self):
        """Worker thread executes assistant inference and emits response_ready."""
        cid = self.assistant.start_conversation()
        worker = AssistantWorker(self.assistant, cid, "Test prompt")

        received_reply = None

        def on_reply(reply):
            nonlocal received_reply
            received_reply = reply

        worker.response_ready.connect(on_reply)
        worker.run()  # Run synchronously in test

        self.assertIsNotNone(received_reply)
        self.assertIn("received your message", received_reply)


if __name__ == "__main__":
    unittest.main()
