# ai_analyser_widget.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QApplication
)
from PyQt5.QtCore import QTimer, pyqtSignal
import threading
import requests
import json


class AIAnalyserWidget(QWidget):
    # Signals for thread-safe UI updates
    show_answer_signal = pyqtSignal(str)
    show_log_signal = pyqtSignal(str)

    def __init__(self, get_api_key_callback):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Paste an HTTP request below to analyse:"))

        self.req_editor = QTextEdit()
        layout.addWidget(self.req_editor)

        self.analyze_btn = QPushButton("Analyze with Perplexity")
        layout.addWidget(self.analyze_btn)

        self.result_label = QLabel("Result will appear below.")
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_box)

        self.analyze_btn.clicked.connect(self.analyze_request)
        self.get_api_key_callback = get_api_key_callback

        # Connect signals to slots that update the UI safely on the main thread
        self.show_answer_signal.connect(self._show_answer_on_main)
        self.show_log_signal.connect(self._append_log_on_main)

    def analyze_request(self):
        req_text = self.req_editor.toPlainText().strip()
        api_key = self.get_api_key_callback()
        if not api_key:
            self.show_log_signal.emit("Please configure your Perplexity API key in the Proxy Config tab.")
            return
        if not req_text:
            self.show_log_signal.emit("Paste an HTTP request first.")
            return

        self.result_box.clear()
        self.show_log_signal.emit("Starting analysis with Perplexity...")

        threading.Thread(target=self._call_perplexity_api, args=(api_key, req_text), daemon=True).start()

    def _call_perplexity_api(self, api_key, req_text):
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        prompt = (
            "Analyze the following HTTP request for web application security vulnerabilities. "
            "Identify any risks (e.g. injection, authentication, sensitive data, etc.) and suggest mitigations. "
            "HTTP request:\n\n" + req_text
        )
        payload = {
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": "You are a security analyst."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.2,
            "stream": False
        }
        try:
            self.show_log_signal.emit("Sending request to Perplexity API...")
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            self.show_log_signal.emit(f"HTTP {resp.status_code} response received from Perplexity.")
            if resp.status_code == 200:
                data = resp.json()
                answer = ""
                if "choices" in data and data["choices"]:
                    answer = data["choices"][0]["message"]["content"]
                    print(answer)
                if not answer:
                    answer = json.dumps(data, indent=2)
                self.show_answer_signal.emit(answer)
                self.show_log_signal.emit("Analysis completed successfully.")
            else:
                self.show_log_signal.emit(f"API Error {resp.status_code}: {resp.text}")
                self.show_answer_signal.emit(f"API Error {resp.status_code}: {resp.text}")
        except Exception as e:
            self.show_log_signal.emit(f"Error calling Perplexity API:\n{str(e)}")
            self.show_answer_signal.emit(f"Error calling Perplexity API:\n{str(e)}")

    def _append_log_on_main(self, text):
        current_text = self.result_box.toPlainText()
        new_text = current_text + ("\n" if current_text else "") + text
        self.result_box.setPlainText(new_text)
        self.result_box.verticalScrollBar().setValue(self.result_box.verticalScrollBar().maximum())

    def _show_answer_on_main(self, text):
        current_text = self.result_box.toPlainText()
        separator = "\n\n--- Analysis Result ---\n\n"
        if separator not in current_text:
            new_text = current_text + separator + text
        else:
            new_text = current_text + "\n" + text
        self.result_box.setPlainText(new_text)
        self.result_box.verticalScrollBar().setValue(self.result_box.verticalScrollBar().maximum())
