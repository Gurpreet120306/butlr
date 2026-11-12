import base64
import json
import logging
from pathlib import Path
from urllib.request import Request, urlopen
from typing import Optional

from app.tools.screen import ScreenCaptureManager

logger = logging.getLogger("BUTL-R.Experimental.Vision")


class MultimodalVisionAssistant:
    """Interprets and describes local visual files and desktop screen state using local vision models."""

    def __init__(
        self,
        model: str = "llama3.2-vision:latest",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        screen_manager: Optional[ScreenCaptureManager] = None,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.screen_manager = screen_manager or ScreenCaptureManager()

    def encode_image(self, file_path: str) -> str:
        """Convert an image file into base64 format for multimodal LLMs."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {file_path}")
        return base64.b64encode(path.read_bytes()).decode("utf-8")

    def analyze_image(self, file_path: str, prompt: str = "Describe what you see in this image in detail.") -> str:
        """Send base64 image and prompt to local vision model."""
        b64_image = self.encode_image(file_path)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [b64_image],
                }
            ],
            "stream": False,
        }

        req = Request(
            url=f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("message", {}).get("content", "").strip()
        except Exception as error:
            logger.error(f"Vision analysis error: {error}")
            return f"Error during vision analysis: {error}"

    def capture_and_analyze(
        self,
        prompt: str = "Analyze what is shown on this screen and identify any errors, notifications, or active windows.",
        filename: Optional[str] = None,
    ) -> tuple[str, str]:
        """Capture the current desktop display and immediately analyze it with the vision model.
        
        Returns a tuple of (screenshot_path, analysis_result).
        """
        screenshot_path = self.screen_manager.capture_screen(filename=filename)
        analysis = self.analyze_image(screenshot_path, prompt=prompt)
        return screenshot_path, analysis
