import logging
from typing import Optional, Any

from app.voice.tts import BaseTTSProvider, WindowsTTSProvider, MockTTSProvider
from app.voice.stt import BaseSTTProvider, MockSTTProvider, WhisperSTTProvider

logger = logging.getLogger("BUTL-R.Voice.Manager")


class VoiceManager:
    """Coordinates Push-to-Talk, Speech-to-Text, and Text-to-Speech interactions."""

    def __init__(
        self,
        tts_provider: Optional[BaseTTSProvider] = None,
        stt_provider: Optional[BaseSTTProvider] = None,
        tts_enabled: bool = True,
    ):
        self.tts = tts_provider if tts_provider is not None else WindowsTTSProvider()
        self.stt = stt_provider if stt_provider is not None else MockSTTProvider()

        self.tts_enabled = tts_enabled
        self.is_listening = False
        self.is_speaking = False

    def start_push_to_talk(self) -> bool:
        """Activate microphone for user voice input."""
        self.is_listening = True
        logger.info("Microphone active: Listening for voice input...")
        return True

    def stop_push_to_talk(self, audio_data: Any = None) -> str:
        """Deactivate microphone and transcribe captured audio to text."""
        self.is_listening = False
        logger.info("Microphone deactivated: Processing speech...")

        if audio_data is not None:
            return self.stt.transcribe(audio_data)

        # In mock or fallback mode with no raw audio stream
        if hasattr(self.stt, "canned_transcript"):
            return self.stt.transcribe(None)

        return ""

    def speak(self, text: str) -> bool:
        """Speak response aloud if TTS is enabled."""
        if not self.tts_enabled or not text or not text.strip():
            return False

        self.is_speaking = True
        success = self.tts.speak(text)
        self.is_speaking = False
        return success

    def toggle_tts(self) -> bool:
        """Toggle text-to-speech voice playback on or off."""
        self.tts_enabled = not self.tts_enabled
        return self.tts_enabled
