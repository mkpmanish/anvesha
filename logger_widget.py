from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHeaderView
)

class LoggerWidget(QWidget):
    def __init__(self, send_to_replay_callback):
        super().__init__()
        self.send_to_replay_callback = send_to_replay_callback

        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Request", "Response"])

        # Set stretch so both columns share half the space
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.table)

        self.send_btn = QPushButton("Send Selected to Replay")
        self.send_btn.clicked.connect(self.send_selected_to_replay)
        layout.addWidget(self.send_btn)

        self.setLayout(layout)

    def send_selected_to_replay(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)  # Request column
            if item:
                req_text = item.text()
                if self.send_to_replay_callback:
                    self.send_to_replay_callback(req_text)

    def log_request(self, req_dict, resp_dict):
        row = self.table.rowCount()
        self.table.insertRow(row)
        req_str = (
            f"{req_dict.get('method', '')} {req_dict.get('url', '')}\n" +
            "\n".join(f"{k}: {v}" for k, v in (req_dict.get('headers') or {}).items()) +
            ("\n\n" + req_dict.get('body', '') if req_dict.get('body', '') else "")
        )
        resp_str = ""
        if resp_dict:
            resp_str = (
                f"HTTP {resp_dict.get('status', '')}\n" +
                "\n".join(f"{k}: {v}" for k, v in (resp_dict.get('headers') or {}).items()) +
                ("\n\n" + resp_dict.get('body', '') if resp_dict.get('body', '') else "")
            )
        self.table.setItem(row, 0, QTableWidgetItem(req_str))
        self.table.setItem(row, 1, QTableWidgetItem(resp_str))
