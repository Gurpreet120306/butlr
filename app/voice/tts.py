import logging
import subprocess
from abc import ABC, abstractmethod

logger = logging.getLogger("BUTL-R.Voice.TTS")


class BaseTTSProvider(ABC):
    """Abstract interface for Text-to-Speech engines."""

    @abstractmethod
    def speak(self, text: str) -> bool:
        """Synthesize and vocalize the given text."""
        pass


class WindowsTTSProvider(BaseTTSProvider):
    """Uses Windows native SAPI SpeechSynthesizer for zero-dependency local TTS."""

    def __init__(self, rate: int = 1, volume: int = 100):
        self.rate = rate  # -10 to 10
        self.volume = volume  # 0 to 100

    def speak(self, text: str) -> bool:
        if not text or not text.strip():
            return False

        clean_text = text.replace("'", "''").replace('"', '`"')
        # Run asynchronously in background process so GUI/CLI is not frozen while speaking
        ps_cmd = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.Rate = {self.rate}; "
            f"$synth.Volume = {self.volume}; "
            f"$synth.Speak('{clean_text}')"
        )
        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as error:
            logger.error(f"Windows TTS error: {error}")
            return False


class PiperTTSProvider(BaseTTSProvider):
    """Integrates Piper fast local neural TTS (planned for high quality CPU speech)."""

    def __init__(self, model_path: str = ""):
        self.model_path = model_path

    def speak(self, text: str) -> bool:
        logger.info(f"Piper neural TTS speaking: {text[:50]}...")
        # Placeholder for Piper binary invocation when user downloads Piper voice models
        return True


class MockTTSProvider(BaseTTSProvider):
    """Mock TTS provider for unit testing without audio hardware."""

    def __init__(self):
        self.last_spoken = ""
        self.speak_count = 0

    def speak(self, text: str) -> bool:
        self.last_spoken = text
        self.speak_count += 1
        return True
