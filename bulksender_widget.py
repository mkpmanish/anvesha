# bulksender_widget.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QLineEdit, QDialog, QDialogButtonBox, QHeaderView, QMessageBox
)
import requests
from urllib.parse import urlparse


class BulkSenderResultsDialog(QDialog):
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bulk Send Results")
        self.resize(600, 400)
        self.parent_widget = parent
        layout = QVBoxLayout(self)

        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Value", "Status", "Content Length"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.results_table)

        btns_layout = QHBoxLayout()
        self.send_to_replay_btn = QPushButton("Send Selected to Replay")
        self.send_to_replay_btn.clicked.connect(self.send_selected_to_replay)
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)

        btns_layout.addWidget(self.send_to_replay_btn)
        btns_layout.addWidget(self.close_btn)
        layout.addLayout(btns_layout)

        self.results = results
        self._requests_text = []
        self.fill_results(results)

    def fill_results(self, results):
        self.results_table.setRowCount(0)
        for value, status, length in results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(value))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(status)))
            self.results_table.setItem(row, 2, QTableWidgetItem(str(length)))

    def set_requests_text(self, requests_text):
        """
        Store the list of request texts corresponding to the results in order,
        so that selected request can be forwarded to Replay tab.
        """
        self._requests_text = requests_text

    def send_selected_to_replay(self):
        row = self.results_table.currentRow()
        if row < 0 or row >= len(self._requests_text):
            QMessageBox.information(self, "No Selection", "Please select a request to send.")
            return

        req_text = self._requests_text[row]

        # Find Replay tab widget in parent main window
        main_win = None
        parent = self.parent_widget
        while parent:
            if hasattr(parent, 'tabs'):
                main_win = parent
                break
            parent = parent.parent()

        if not main_win:
            QMessageBox.warning(self, "Error", "Could not find main window to send request to Replay tab.")
            return

        replay_tab = None
        for i in range(main_win.tabs.count()):
            widget = main_win.tabs.widget(i)
            if widget and widget.__class__.__name__ == 'ReplayWidget':
                replay_tab = widget
                break

        if not replay_tab:
            QMessageBox.warning(self, "Error", "Could not find Replay tab to send request.")
            return

        replay_tab.add_new_tab(req_text)

        index = main_win.tabs.indexOf(replay_tab)
        if index != -1:
            main_win.tabs.setCurrentIndex(index)


class BulkSenderWidget(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)

        # Section 1: Request template (multi-line text)
        req_layout = QVBoxLayout()
        req_label = QLabel("Request Template (use {keyword}):")
        self.req_editor = QTextEdit()
        req_layout.addWidget(req_label)
        req_layout.addWidget(self.req_editor)

        # Section 2 & 3 horizontally: Values and Keyword
        bottom_layout = QHBoxLayout()

        # Values section (multi-line text)
        values_layout = QVBoxLayout()
        values_label = QLabel("Values (one per line):")
        self.values_input = QTextEdit()
        values_layout.addWidget(values_label)
        values_layout.addWidget(self.values_input)

        # Keyword section (single line)
        keyword_layout = QVBoxLayout()
        keyword_label = QLabel("Keyword:")
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("keyword (without braces {})")
        keyword_layout.addWidget(keyword_label)
        keyword_layout.addWidget(self.keyword_input)

        bottom_layout.addLayout(values_layout, 3)
        bottom_layout.addLayout(keyword_layout, 1)

        main_layout.addLayout(req_layout)
        main_layout.addLayout(bottom_layout)

        # Send and Send to Replay buttons
        btn_layout = QHBoxLayout()
        self.send_btn = QPushButton("Send Bulk")
        self.send_btn.clicked.connect(self.send_bulk)
        self.send_replay_btn = QPushButton("Send Bulk to Replay")
        self.send_replay_btn.clicked.connect(self.send_bulk_to_replay)
        btn_layout.addWidget(self.send_btn)
        btn_layout.addWidget(self.send_replay_btn)

        main_layout.addLayout(btn_layout)

        # Store last sent requests with their values for sending to replay
        self.last_sent_requests = []

    def send_bulk(self):
        template = self.req_editor.toPlainText()
        keyword = self.keyword_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "Input Error", "Please enter a keyword.")
            return
        if f"{{{keyword}}}" not in template:
            QMessageBox.warning(self, "Input Error", f"The template does not contain the keyword '{{{keyword}}}'.")
            return

        values = [v.strip() for v in self.values_input.toPlainText().splitlines() if v.strip()]
        if not values:
            QMessageBox.warning(self, "Input Error", "Please enter at least one value.")
            return

        results = []
        sent_requests = []

        for value in values:
            req_text = template.replace(f"{{{keyword}}}", value)
            try:
                lines = [l for l in req_text.strip().splitlines() if l.strip()]
                if not lines:
                    raise Exception("Empty request text")
                first_line = lines[0].strip()
                parts = first_line.split()
                if len(parts) < 2:
                    raise Exception(f"Malformed request line: '{first_line}'")
                method, url = parts[0], parts[1]
                url = url.strip().strip("'\"[]")  # CLEAN UP URL to fix issues

                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise Exception(f"Malformed URL: '{url}'")

                headers = {}
                body_lines = []
                in_headers = True
                for line in lines[1:]:
                    if in_headers and ':' in line:
                        k, v = line.split(':', 1)
                        headers[k.strip()] = v.strip()
                    else:
                        in_headers = False
                        body_lines.append(line)
                body = '\n'.join(body_lines).strip() or None

                resp = requests.request(method, url, headers=headers, data=body, verify=False, timeout=20)
                results.append((value, resp.status_code, len(resp.content)))
                sent_requests.append(req_text)
            except Exception as e:
                results.append((value, "ERR", str(e)))
                sent_requests.append(req_text)

        self.last_sent_requests = sent_requests

        dlg = BulkSenderResultsDialog(results, self)
        dlg.set_requests_text(sent_requests)
        dlg.exec_()

    def send_bulk_to_replay(self):
        if not self.last_sent_requests:
            QMessageBox.information(self, "No Requests Sent", "Please send bulk requests first before sending to Replay.")
            return

        main_win = self.parent()
        while main_win and not hasattr(main_win, 'tabs'):
            main_win = main_win.parent()

        if not main_win:
            QMessageBox.warning(self, "Replay Tab Not Found", "Could not find main window to send requests.")
            return

        replay_tab = None
        for i in range(main_win.tabs.count()):
            widget = main_win.tabs.widget(i)
            if widget and widget.__class__.__name__ == 'ReplayWidget':
                replay_tab = widget
                break

        if not replay_tab:
            QMessageBox.warning(self, "Replay Tab Not Found", "Could not find Replay tab to send requests.")
            return

        for req_text in self.last_sent_requests:
            replay_tab.add_new_tab(req_text)

        index = main_win.tabs.indexOf(replay_tab)
        if index != -1:
            main_win.tabs.setCurrentIndex(index)

    def add_request(self, req_text):
        self.req_editor.setPlainText(req_text)
        self.values_input.clear()
        self.keyword_input.clear()
        self.last_sent_requests = [req_text]
