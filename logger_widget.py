# logger_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView

class LoggerWidget(QWidget):
    def __init__(self, send_to_replay_callback):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['Request', 'Response'])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.send_to_replay_callback = send_to_replay_callback
        btn = QPushButton("Send Selected to Replay (Ctrl+R)")
        btn.clicked.connect(self.send_selected)
        layout.addWidget(self.table)
        layout.addWidget(btn)

    def log_request(self, req_dict, resp_dict):
        row = self.table.rowCount()
        self.table.insertRow(row)
        req_str = (
            f"{req_dict.get('method', '')} {req_dict.get('url', '')}\n" +
            "\n".join(f"{k}: {v}" for k, v in req_dict.get('headers', {}).items()) +
            ("\n\n" + req_dict.get('body', '') if req_dict.get('body', '') else "")
        )
        resp_str = ""
        if resp_dict:
            resp_str = (
                f"HTTP {resp_dict.get('status', '')}\n" +
                "\n".join(f"{k}: {v}" for k, v in resp_dict.get('headers', {}).items()) +
                ("\n\n" + resp_dict.get('body', '') if resp_dict.get('body', '') else "")
            )
        self.table.setItem(row, 0, QTableWidgetItem(req_str))
        self.table.setItem(row, 1, QTableWidgetItem(resp_str))

    def send_selected(self):
        row = self.table.currentRow()
        if row != -1:
            req_item = self.table.item(row, 0)
            if req_item:
                self.send_to_replay_callback(req_item.text())
