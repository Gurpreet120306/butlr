from PySide6.QtCore import QThread, Signal


class AssistantWorker(QThread):
    """Background worker thread to run AI inference without blocking the GUI."""

    response_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, assistant, conversation_id: str, message: str):
        super().__init__()
        self.assistant = assistant
        self.conversation_id = conversation_id
        self.message = message

    def run(self):
        try:
            reply = self.assistant.send_message(
                self.conversation_id,
                self.message,
            )
            self.response_ready.emit(reply)
        except Exception as error:
            self.error_occurred.emit(str(error))
