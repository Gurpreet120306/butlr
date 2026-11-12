"""BUTL-R Voice Capabilities: STT, TTS, and Push-to-Talk."""

from app.voice.tts import BaseTTSProvider, WindowsTTSProvider, MockTTSProvider
from app.voice.stt import BaseSTTProvider, MockSTTProvider, WhisperSTTProvider
from app.voice.manager import VoiceManager
from app.voice.wakeword import WakeWordDetector

__all__ = [
    "BaseTTSProvider",
    "WindowsTTSProvider",
    "MockTTSProvider",
    "BaseSTTProvider",
    "MockSTTProvider",
    "WhisperSTTProvider",
    "VoiceManager",
    "WakeWordDetector",
]
