import unittest
from unittest.mock import MagicMock

from app.voice.wakeword import WakeWordDetector


class TestWakeWordDetection(unittest.TestCase):

    def test_wake_word_activation_and_detection(self):
        """Wake-word detector triggers callback when configured wake phrase is heard."""
        callback = MagicMock()
        detector = WakeWordDetector(
            wake_words={"hey butler", "jarvis"},
            on_detected=callback,
        )

        # Before activation, nothing happens
        self.assertFalse(detector.process_text_frame("hey butler, what is the time?"))
        callback.assert_not_called()

        # After activation
        detector.start_listening()
        self.assertTrue(detector.is_active)

        detected = detector.process_text_frame("Hey Butler, check my messages.")
        self.assertTrue(detected)
        callback.assert_called_once()

    def test_wake_word_ignores_unrelated_speech(self):
        """Unrelated speech does not trigger wake word callback."""
        callback = MagicMock()
        detector = WakeWordDetector(
            wake_words={"hey butler"},
            on_detected=callback,
        )
        detector.start_listening()

        detected = detector.process_text_frame("Can you open the door please?")
        self.assertFalse(detected)
        callback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
