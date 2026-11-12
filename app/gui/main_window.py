import html
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.gui.worker import AssistantWorker
from app.voice.manager import VoiceManager


DARK_STYLESHEET = """
QMainWindow {
    background-color: #0f1117;
}

QWidget {
    font-family: 'Segoe UI', system-ui, sans-serif;
    color: #e5e7eb;
}

QFrame#sidebar {
    background-color: #161922;
    border-right: 1px solid #232733;
}

QFrame#topbar {
    background-color: #161922;
    border-bottom: 1px solid #232733;
}

QTextBrowser {
    background-color: #0f1117;
    border: none;
    padding: 16px;
    font-size: 13px;
    line-height: 1.6;
}

QLineEdit {
    background-color: #1e2230;
    border: 1px solid #2c3245;
    border-radius: 8px;
    padding: 10px 14px;
    color: #ffffff;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #3b82f6;
}

QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #1e293b;
    color: #64748b;
}

QPushButton.secondary-btn {
    background-color: #1e2230;
    border: 1px solid #2c3245;
    color: #cbd5e1;
    text-align: left;
    padding: 10px 14px;
}

QPushButton.secondary-btn:hover {
    background-color: #262c3e;
    color: #ffffff;
}

QPushButton.mode-btn-active {
    background-color: #059669;
    border: 1px solid #10b981;
    color: #ffffff;
}

QStatusBar {
    background-color: #161922;
    color: #94a3b8;
    border-top: 1px solid #232733;
    font-size: 11px;
}
"""


class ButlrMainWindow(QMainWindow):
    """Main desktop graphical interface for BUTL-R."""

    def __init__(self, assistant, voice_manager=None):
        super().__init__()
        self.assistant = assistant
        self.voice_manager = voice_manager if voice_manager is not None else VoiceManager()
        self.conversation_id = assistant.start_conversation()
        self.worker = None

        self.setWindowTitle("BUTL-R — Personal AI Assistant")
        self.resize(1000, 700)
        self.setStyleSheet(DARK_STYLESHEET)

        self._build_ui()
        self._update_status_display()
        self._append_system_message("BUTL-R Online. Voice and desktop systems operational.")

    def _build_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ------------------ SIDEBAR ------------------
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 20)
        sidebar_layout.setSpacing(12)

        # Brand header
        brand_label = QLabel("BUTL-R")
        brand_font = QFont()
        brand_font.setPointSize(16)
        brand_font.setBold(True)
        brand_label.setFont(brand_font)
        brand_label.setStyleSheet("color: #60a5fa; letter-spacing: 2px;")
        sidebar_layout.addWidget(brand_label)

        subtitle_label = QLabel("Personal AI Assistant")
        subtitle_label.setStyleSheet("color: #64748b; font-size: 11px; margin-bottom: 8px;")
        sidebar_layout.addWidget(subtitle_label)

        # Action: New Chat
        new_chat_btn = QPushButton("+ New Conversation")
        new_chat_btn.setObjectName("new_chat_btn")
        new_chat_btn.clicked.connect(self._on_new_conversation)
        sidebar_layout.addWidget(new_chat_btn)

        # Separator label
        model_sec_label = QLabel("AI MODEL MODE")
        model_sec_label.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold; margin-top: 14px;")
        sidebar_layout.addWidget(model_sec_label)

        # Mode Buttons
        self.fast_mode_btn = QPushButton("⚡ Fast Mode (1B)")
        self.fast_mode_btn.setProperty("class", "secondary-btn")
        self.fast_mode_btn.clicked.connect(lambda: self._switch_mode("fast"))
        sidebar_layout.addWidget(self.fast_mode_btn)

        self.quality_mode_btn = QPushButton("🧠 Quality Mode (4B)")
        self.quality_mode_btn.setProperty("class", "secondary-btn")
        self.quality_mode_btn.clicked.connect(lambda: self._switch_mode("quality"))
        sidebar_layout.addWidget(self.quality_mode_btn)

        # Privacy & Tools Section
        tools_sec_label = QLabel("DATA & PRIVACY")
        tools_sec_label.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold; margin-top: 14px;")
        sidebar_layout.addWidget(tools_sec_label)

        self.screen_btn = QPushButton("📸 Screen Analysis")
        self.screen_btn.setProperty("class", "secondary-btn")
        self.screen_btn.clicked.connect(self._analyze_screen)
        sidebar_layout.addWidget(self.screen_btn)

        self.debug_btn = QPushButton("🐞 Smart Debugger")
        self.debug_btn.setProperty("class", "secondary-btn")
        self.debug_btn.clicked.connect(self._run_smart_debugger)
        sidebar_layout.addWidget(self.debug_btn)

        self.voice_toggle_btn = QPushButton("🔊 Voice Output: ON")
        self.voice_toggle_btn.setProperty("class", "secondary-btn")
        self.voice_toggle_btn.clicked.connect(self._toggle_voice_output)
        sidebar_layout.addWidget(self.voice_toggle_btn)

        export_btn = QPushButton("📁 Export Data (JSON)")
        export_btn.setProperty("class", "secondary-btn")
        export_btn.clicked.connect(self._export_data)
        sidebar_layout.addWidget(export_btn)

        clear_btn = QPushButton("🗑️ Clear History")
        clear_btn.setProperty("class", "secondary-btn")
        clear_btn.clicked.connect(self._clear_conversation)
        sidebar_layout.addWidget(clear_btn)

        sidebar_layout.addStretch()

        # Local Privacy Badge
        privacy_badge = QLabel("🛡️ Local-Only Mode: ON")
        privacy_badge.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold; padding: 8px; background: #064e3b; border-radius: 6px;")
        sidebar_layout.addWidget(privacy_badge)

        main_layout.addWidget(sidebar)

        # ------------------ CHAT AREA ------------------
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Top bar
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(50)
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(20, 0, 20, 0)

        self.top_status_label = QLabel("Initializing BUTL-R...")
        self.top_status_label.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        topbar_layout.addWidget(self.top_status_label)
        topbar_layout.addStretch()

        self.activity_label = QLabel("Ready")
        self.activity_label.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold;")
        topbar_layout.addWidget(self.activity_label)

        chat_layout.addWidget(topbar)

        # Chat message log
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        chat_layout.addWidget(self.chat_display)

        # Message input bar
        input_container = QFrame()
        input_container.setStyleSheet("background-color: #161922; border-top: 1px solid #232733; padding: 12px 20px;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Ask BUTL-R or hold 'Push to Talk'...")
        self.message_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.message_input)

        self.ptt_button = QPushButton("🎤 Push to Talk")
        self.ptt_button.setFixedWidth(120)
        self.ptt_button.setStyleSheet("background-color: #374151; color: #ffffff;")
        self.ptt_button.pressed.connect(self._on_ptt_pressed)
        self.ptt_button.released.connect(self._on_ptt_released)
        input_layout.addWidget(self.ptt_button)

        self.screen_quick_btn = QPushButton("📸 Screen")
        self.screen_quick_btn.setFixedWidth(85)
        self.screen_quick_btn.setStyleSheet("background-color: #0f766e; color: #ffffff;")
        self.screen_quick_btn.clicked.connect(self._analyze_screen)
        input_layout.addWidget(self.screen_quick_btn)

        self.send_button = QPushButton("Send")
        self.send_button.setFixedWidth(80)
        self.send_button.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_button)

        chat_layout.addWidget(input_container)
        main_layout.addWidget(chat_container)

        self.setCentralWidget(main_widget)

    def _update_status_display(self):
        mode = self.assistant.get_mode().upper()
        self.top_status_label.setText(f"Mode: <b>{mode}</b> | Storage: <b>MongoDB</b> | Runtime: <b>Ollama (CPU)</b>")

    def _append_message(self, sender: str, text: str, is_user: bool = False):
        time_str = datetime.now().strftime("%H:%M")
        escaped_text = html.escape(text).replace("\n", "<br>")

        if is_user:
            bubble = f"""
            <div style='margin-bottom: 14px; text-align: right;'>
                <div style='display: inline-block; background-color: #1d4ed8; color: #ffffff; padding: 10px 14px; border-radius: 12px; max-width: 75%; text-align: left;'>
                    <div style='font-size: 11px; opacity: 0.8; margin-bottom: 4px; font-weight: bold;'>You • {time_str}</div>
                    <div style='font-size: 13px;'>{escaped_text}</div>
                </div>
            </div>
            """
        else:
            bubble = f"""
            <div style='margin-bottom: 14px; text-align: left;'>
                <div style='display: inline-block; background-color: #1e2230; border: 1px solid #2d3345; color: #e2e8f0; padding: 12px 16px; border-radius: 12px; max-width: 80%;'>
                    <div style='font-size: 11px; color: #60a5fa; margin-bottom: 4px; font-weight: bold;'>BUTL-R • {time_str}</div>
                    <div style='font-size: 13px; line-height: 1.5;'>{escaped_text}</div>
                </div>
            </div>
            """

        self.chat_display.append(bubble)
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def _append_system_message(self, text: str):
        bubble = f"""
        <div style='margin: 10px 0; text-align: center;'>
            <span style='background-color: #1e293b; color: #94a3b8; padding: 4px 12px; border-radius: 12px; font-size: 11px;'>
                {html.escape(text)}
            </span>
        </div>
        """
        self.chat_display.append(bubble)

    def _send_message(self):
        text = self.message_input.text().strip()
        if not text:
            return

        self._append_message("You", text, is_user=True)
        self.message_input.clear()
        self.message_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.activity_label.setText("Thinking...")
        self.activity_label.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: bold;")

        # Run AI generation in background thread to keep GUI smooth
        self.worker = AssistantWorker(self.assistant, self.conversation_id, text)
        self.worker.response_ready.connect(self._on_response_ready)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.start()

    def _on_response_ready(self, reply: str):
        self._append_message("BUTL-R", reply, is_user=False)
        self.message_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.message_input.setFocus()
        self.activity_label.setText("Ready")
        self.activity_label.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold;")

        # Vocalize response if voice output is enabled
        self.voice_manager.speak(reply)

    def _on_ptt_pressed(self):
        """Microphone key held down: start listening."""
        self.voice_manager.start_push_to_talk()
        self.ptt_button.setText("🔴 Listening...")
        self.ptt_button.setStyleSheet("background-color: #dc2626; color: #ffffff; font-weight: bold;")
        self.activity_label.setText("🎙️ Microphone Active")
        self.activity_label.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: bold;")

    def _on_ptt_released(self):
        """Microphone key released: stop listening and transcribe."""
        self.ptt_button.setText("🎤 Push to Talk")
        self.ptt_button.setStyleSheet("background-color: #374151; color: #ffffff;")
        self.activity_label.setText("Ready")
        self.activity_label.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold;")

        transcribed = self.voice_manager.stop_push_to_talk()
        if transcribed and transcribed.strip():
            self.message_input.setText(transcribed.strip())
            self._send_message()

    def _toggle_voice_output(self):
        """Toggle audio readout on or off."""
        is_on = self.voice_manager.toggle_tts()
        status_text = "ON" if is_on else "OFF"
        icon = "🔊" if is_on else "🔇"
        self.voice_toggle_btn.setText(f"{icon} Voice Output: {status_text}")

    def _on_worker_error(self, err_msg: str):
        self._append_message("BUTL-R", f"Error: {err_msg}", is_user=False)
        self.message_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.activity_label.setText("Error")
        self.activity_label.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: bold;")

    def _switch_mode(self, mode: str):
        try:
            model = self.assistant.set_mode(mode)
            self._update_status_display()
            self._append_system_message(f"Switched to {mode.upper()} MODE ({model})")
        except Exception as error:
            QMessageBox.warning(self, "Mode Switch Error", str(error))

    def _on_new_conversation(self):
        self.conversation_id = self.assistant.start_conversation()
        self.chat_display.clear()
        self._append_system_message("Started a new conversation.")

    def _clear_conversation(self):
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to delete this conversation's messages?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.assistant.delete_conversation(self.conversation_id)
            self.conversation_id = self.assistant.start_conversation()
            self.chat_display.clear()
            self._append_system_message("Conversation cleared.")

    def _export_data(self):
        data = self.assistant.export_data()
        QMessageBox.information(
            self,
            "Data Export Complete",
            f"Successfully exported:\n- {data['conversations_count']} Conversations\n- {data['messages_count']} Messages\n- {data['memories_count']} Saved Memories\n\nPrivacy Mode: {data['privacy_mode']}",
        )

    def _analyze_screen(self):
        """Observe: Capture current desktop screen and analyze with multimodal vision."""
        self._append_system_message("📸 Capturing desktop screen and analyzing with vision model...")
        self.activity_label.setText("Analyzing Screen...")
        self.activity_label.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: bold;")
        try:
            from app.experimental.multimodal import MultimodalVisionAssistant
            vision = MultimodalVisionAssistant()
            screenshot_path, analysis = vision.capture_and_analyze(
                prompt="Examine what is visible on this screen. Describe active applications, identify any visible errors or notices, and summarize what the user is working on."
            )
            self._append_message("BUTL-R Vision", f"**Screen Capture Analysis** (Saved to `{screenshot_path}`):\n\n{analysis}", is_user=False)
            if self.voice_manager and self.voice_manager.tts_enabled:
                self.voice_manager.speak(f"Screen analyzed. {analysis[:140]}")
        except Exception as error:
            self._append_message("BUTL-R", f"Screen analysis error: {error}", is_user=False)
        finally:
            self.activity_label.setText("Ready")
            self.activity_label.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold;")

    def _run_smart_debugger(self):
        """Diagnose code or website errors."""
        text, ok = QInputDialog.getMultiLineText(
            self,
            "Smart Debugger (HACKNAUTS 2.0)",
            "Paste code snippet, website URL, or error traceback to diagnose:",
            "TypeError: Cannot read properties of undefined (reading 'map')"
        )
        if ok and text.strip():
            from app.intelligence.debugger import SmartDebugger
            debugger = SmartDebugger(ai_provider=self.assistant.provider_manager.get_provider())
            result = debugger.diagnose_error(text.strip())
            summary = (
                f"**🐞 Debugger Diagnostic Result**:\n"
                f"- **Error Type:** `{result.get('error_type')}`\n"
                f"- **Explanation:** {result.get('explanation')}\n"
                f"- **Recommended Fix:**\n```\n{result.get('suggested_fix')}\n```"
            )
            self._append_message("BUTL-R Debugger", summary, is_user=False)
            if self.voice_manager and self.voice_manager.tts_enabled:
                self.voice_manager.speak(f"Error diagnosed: {result.get('error_type')}. {result.get('explanation')}")
