from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QLineEdit, QHeaderView, QLabel, QHBoxLayout
)
from PyQt5.QtCore import Qt

class LoggerWidget(QWidget):
    def __init__(self, send_to_replay_callback, send_to_bulk_callback):
        super().__init__()
        self.send_to_replay_callback = send_to_replay_callback
        self.send_to_bulk_callback = send_to_bulk_callback

        main_layout = QVBoxLayout()

        # Search bar layout with Clear button
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search requests or responses")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_btn)
        main_layout.addLayout(search_layout)

        # Table with columns: ID, Timestamp, Request, Response
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Request ID", "Timestamp", "Request", "Response"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        main_layout.addWidget(self.table)

        # Send buttons
        btn_layout = QHBoxLayout()
        self.send_btn = QPushButton("Send Selected to Replay")
        self.send_btn.clicked.connect(self.send_selected_to_replay)
        btn_layout.addWidget(self.send_btn)

        self.send_bulk_btn = QPushButton("Send Selected to Bulk Sender")
        self.send_bulk_btn.clicked.connect(self.send_selected_to_bulk)
        btn_layout.addWidget(self.send_bulk_btn)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self.all_rows = []

    def send_selected_to_replay(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 2)
            if item and self.send_to_replay_callback:
                req_text = item.text()
                self.send_to_replay_callback(req_text)

    def send_selected_to_bulk(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 2)
            if item and self.send_to_bulk_callback:
                req_text = item.text()
                self.send_to_bulk_callback(req_text)

    def log_request(self, req_dict, resp_dict):
        req_id = req_dict.get("id", "")
        timestamp = req_dict.get("timestamp", "")
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
        self.all_rows.append((req_id, timestamp, req_str, resp_str))

        if self.filter_match(req_str, resp_str, self.search_input.text()):
            self._add_row(req_id, timestamp, req_str, resp_str)

    def _add_row(self, req_id, timestamp, req_str, resp_str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(req_id))
        self.table.setItem(row, 1, QTableWidgetItem(timestamp))
        self.table.setItem(row, 2, QTableWidgetItem(req_str))
        self.table.setItem(row, 3, QTableWidgetItem(resp_str))

    def on_search_text_changed(self, text):
        text = text.lower()
        self.table.setRowCount(0)
        for req_id, timestamp, req_str, resp_str in self.all_rows:
            if self.filter_match(req_str, resp_str, text):
                self._add_row(req_id, timestamp, req_str, resp_str)

    def filter_match(self, req_str, resp_str, text):
        if not text:
            return True
        return text in req_str.lower() or text in resp_str.lower()

    def on_clear_clicked(self):
        self.search_input.clear()

    def clear_all(self):
        self.table.setRowCount(0)
        self.all_rows.clear()

    def parse_req_resp_to_dict(self, req_id, timestamp, req_str):
        lines = req_str.strip().split("\n")
        if not lines:
            return {}
        method_url = lines[0].split(" ", 1)
        method = method_url if len(method_url) > 0 else ""
        url = method_url if len(method_url) > 1 else ""
        headers, body = {}, ""
        parsing_headers = True
        for line in lines[1:]:
            if parsing_headers and ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip()] = v.strip()
            else:
                parsing_headers = False
                body += line + "\n"
        return {
            "id": req_id,
            "timestamp": timestamp,
            "method": method,
            "url": url,
            "headers": headers,
            "body": body.strip()
        }

    def parse_resp_str_to_dict(self, resp_str):
        lines = resp_str.strip().split("\n")
        status_line = lines[0] if lines else ""
        status = ""
        if status_line.startswith("HTTP"):
            parts = status_line.split()
            if len(parts) > 1:
                status = parts
        headers, body = {}, ""
        parsing_headers = True
        for line in lines[1:]:
            if parsing_headers and ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip()] = v.strip()
            else:
                parsing_headers = False
                body += line + "\n"
        return {
            "status": status,
            "headers": headers,
            "body": body.strip()
        }
