from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QHeaderView, QLabel, QHBoxLayout
)
from PyQt5.QtCore import Qt

class LoggerWidget(QWidget):
    def __init__(self, send_to_replay_callback):
        super().__init__()
        self.send_to_replay_callback = send_to_replay_callback

        main_layout = QVBoxLayout()

        # Search bar layout
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search requests or responses")
        self.search_input.textChanged.connect(self.on_search_text_changed)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Request", "Response"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        main_layout.addWidget(self.table)

        # Send to Replay button
        self.send_btn = QPushButton("Send Selected to Replay")
        self.send_btn.clicked.connect(self.send_selected_to_replay)
        main_layout.addWidget(self.send_btn)

        self.setLayout(main_layout)

        # Store all rows for filtering
        self.all_rows = []

    def send_selected_to_replay(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)  # Request column
            if item:
                req_text = item.text()
                if self.send_to_replay_callback:
                    self.send_to_replay_callback(req_text)

    def log_request(self, req_dict, resp_dict):
        req_str = (
            f"{req_dict.get('method', '')} {req_dict.get('url', '')}\n" +
            "\n".join(f"{k}: {v}" for k, v in (req_dict.get('headers') or {}).items()) +
            ("\n\n" + req_dict.get('body', '') if req_dict.get('body') else "")
        )
        resp_str = ""
        if resp_dict:
            resp_str = (
                f"HTTP {resp_dict.get('status', '')}\n" +
                "\n".join(f"{k}: {v}" for k, v in (resp_dict.get('headers') or {}).items()) +
                ("\n\n" + resp_dict.get('body', '') if resp_dict.get('body') else "")
            )
        # Store the raw strings to allow filtering later
        self.all_rows.append((req_str, resp_str))

        # Add row to the UI table if it matches current filter (or if no filter)
        if self.filter_match(req_str, resp_str, self.search_input.text()):
            self._add_row(req_str, resp_str)

    def _add_row(self, req_str, resp_str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(req_str))
        self.table.setItem(row, 1, QTableWidgetItem(resp_str))

    def on_search_text_changed(self, text):
        text = text.lower()
        self.table.setRowCount(0)
        for req_str, resp_str in self.all_rows:
            if self.filter_match(req_str, resp_str, text):
                self._add_row(req_str, resp_str)

    def filter_match(self, req_str, resp_str, text):
        if not text:
            return True
        return text in req_str.lower() or text in resp_str.lower()
