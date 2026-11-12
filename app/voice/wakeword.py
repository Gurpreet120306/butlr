import logging
from typing import Callable, Optional

logger = logging.getLogger("BUTL-R.Voice.WakeWord")


class WakeWordDetector:
    """Detects spoken wake words (e.g. 'Hey Butler') to activate the assistant."""

    DEFAULT_WAKE_WORDS = {"hey butler", "butler", "jarvis"}

    def __init__(
        self,
        wake_words: Optional[set[str]] = None,
        on_detected: Optional[Callable[[], None]] = None,
        sensitivity: float = 0.5,
    ):
        self.wake_words = wake_words or set(self.DEFAULT_WAKE_WORDS)
        self.on_detected = on_detected
        self.sensitivity = sensitivity
        self.is_active = False

    def start_listening(self) -> None:
        """Start listening for configured wake words."""
        self.is_active = True
        logger.info(f"Wake-word engine active. Listening for: {self.wake_words}")

    def stop_listening(self) -> None:
        """Stop wake-word detection."""
        self.is_active = False
        logger.info("Wake-word engine deactivated.")

    def process_text_frame(self, frame_text: str) -> bool:
        """Check if incoming spoken text frame matches any active wake word."""
        if not self.is_active or not frame_text:
            return False

        normalized = frame_text.lower().strip()
        for ww in self.wake_words:
            if ww in normalized:
                logger.info(f"Wake word detected: '{ww}'")
                if self.on_detected:
                    self.on_detected()
                return True

        return False
