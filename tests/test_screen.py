import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.tools.screen import ScreenCaptureManager
from app.experimental.multimodal import MultimodalVisionAssistant


class TestScreenCapture(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = ScreenCaptureManager(output_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_capture_screen_creates_file(self):
        path = self.manager.capture_screen(filename="test_shot.png")
        self.assertTrue(Path(path).exists())
        self.assertGreater(Path(path).stat().st_size, 0)

    @patch("app.experimental.multimodal.urlopen")
    def test_multimodal_capture_and_analyze(self, mock_urlopen):
        # Mock vision model response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": "Visible: A browser window with an error."}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        vision = MultimodalVisionAssistant(screen_manager=self.manager)
        shot_path, analysis = vision.capture_and_analyze(
            prompt="Find errors on screen",
            filename="analysis_test.png",
        )

        self.assertTrue(Path(shot_path).exists())
        self.assertIn("Visible: A browser window with an error", analysis)


if __name__ == "__main__":
    unittest.main()
