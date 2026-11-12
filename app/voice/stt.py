import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger("BUTL-R.Voice.STT")


class BaseSTTProvider(ABC):
    """Abstract interface for Speech-to-Text engines."""

    @abstractmethod
    def transcribe(self, audio_data: Any) -> str:
        """Convert captured audio into text."""
        pass


class WhisperSTTProvider(BaseSTTProvider):
    """Integrates faster-whisper quantized for low-latency CPU transcription."""

    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None

    def _ensure_loaded(self):
        if self.model is None:
            try:
                from faster_whisper import WhisperModel
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
            except ImportError:
                logger.warning("faster-whisper is not installed. Using fallback transcription.")
                self.model = False

    def transcribe(self, audio_data: Any) -> str:
        self._ensure_loaded()
        if not self.model:
            return ""

        segments, _ = self.model.transcribe(audio_data, beam_size=1)
        return " ".join(segment.text for segment in segments).strip()


class MockSTTProvider(BaseSTTProvider):
    """Mock STT provider for automated testing without microphone."""

    def __init__(self, canned_transcript: str = "Hello BUTL-R"):
        self.canned_transcript = canned_transcript
        self.call_count = 0

    def set_transcript(self, text: str):
        self.canned_transcript = text

    def transcribe(self, audio_data: Any) -> str:
        self.call_count += 1
        return self.canned_transcript
