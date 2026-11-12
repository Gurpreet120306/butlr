import os
import unittest
from mongomock import MongoClient

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication

from app.voice.tts import MockTTSProvider, WindowsTTSProvider
from app.voice.stt import MockSTTProvider
from app.voice.manager import VoiceManager
from app.assistant.engine import ButlrAssistant
from app.assistant.conversation import ConversationManager
from app.assistant.memory import MemoryManager
from app.assistant.providers import MockAIProvider
from app.gui.main_window import ButlrMainWindow
from app.security.policy import SecurityPolicy
from app.security.audit import AuditLogger
from app.security.privacy import PrivacyManager


class TestVoiceSubsystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])

    def setUp(self):
        self.tts = MockTTSProvider()
        self.stt = MockSTTProvider(canned_transcript="Hello BUTL-R through voice")
        self.voice_mgr = VoiceManager(
            tts_provider=self.tts,
            stt_provider=self.stt,
            tts_enabled=True,
        )

    def test_mock_tts_speak(self):
        """TTS provider speaks and records spoken text."""
        result = self.voice_mgr.speak("Good morning sir.")
        self.assertTrue(result)
        self.assertEqual(self.tts.last_spoken, "Good morning sir.")
        self.assertEqual(self.tts.speak_count, 1)

    def test_tts_toggle_mute(self):
        """Muting TTS prevents audio output."""
        self.voice_mgr.toggle_tts()
        self.assertFalse(self.voice_mgr.tts_enabled)

        result = self.voice_mgr.speak("This should be silent.")
        self.assertFalse(result)
        self.assertEqual(self.tts.speak_count, 0)

    def test_push_to_talk_workflow(self):
        """Push-to-talk activates microphone then transcribes speech on release."""
        self.voice_mgr.start_push_to_talk()
        self.assertTrue(self.voice_mgr.is_listening)

        transcript = self.voice_mgr.stop_push_to_talk()
        self.assertFalse(self.voice_mgr.is_listening)
        self.assertEqual(transcript, "Hello BUTL-R through voice")

    def test_windows_tts_empty_input_rejected(self):
        """WindowsTTSProvider gracefully ignores empty input."""
        win_tts = WindowsTTSProvider()
        self.assertFalse(win_tts.speak("   "))
        self.assertFalse(win_tts.speak(""))

    def test_gui_voice_ptt_interaction(self):
        """GUI PTT button triggers speech transcription and message send."""
        client = MongoClient()
        database = client["butlr_gui_voice_test"]
        assistant = ButlrAssistant(
            provider=MockAIProvider(),
            conversation_manager=ConversationManager(database=database),
            memory_manager=MemoryManager(database=database),
            security_policy=SecurityPolicy(),
            audit_logger=AuditLogger(database=database),
            privacy_manager=PrivacyManager(database=database),
        )

        window = ButlrMainWindow(assistant, voice_manager=self.voice_mgr)

        # Press PTT
        window._on_ptt_pressed()
        self.assertTrue(self.voice_mgr.is_listening)
        self.assertIn("Listening", window.ptt_button.text())

        # Release PTT
        window._on_ptt_released()
        self.assertFalse(self.voice_mgr.is_listening)
        self.assertIn("Push to Talk", window.ptt_button.text())

        # Verify chat contains transcribed voice message
        html_content = window.chat_display.toHtml()
        self.assertIn("Hello BUTL-R through voice", html_content)

        window.close()
        client.close()


if __name__ == "__main__":
    unittest.main()
