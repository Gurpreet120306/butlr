import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.assistant.engine import ButlrAssistant
from app.assistant.ollama_provider import OllamaProvider
from app.gui.main_window import ButlrMainWindow


def run_gui(assistant=None):
    """Launch the BUTL-R desktop GUI application."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    if assistant is None:
        provider = OllamaProvider(model="gemma3:4b", timeout=180)
        assistant = ButlrAssistant(provider=provider)

    window = ButlrMainWindow(assistant)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())
