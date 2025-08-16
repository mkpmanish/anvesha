# bulksender_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QLineEdit
import requests

class BulkSenderWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.req_editor = QTextEdit()
        self.param_input = QLineEdit()
        self.values_input = QTextEdit()
        self.send_btn = QPushButton("Send Bulk")
        self.send_btn.clicked.connect(self.send_bulk)
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(['Value', 'Status', 'Content Length'])

        self.layout().addWidget(QLabel("Request template (use {param}):"))
        self.layout().addWidget(self.req_editor)
        self.layout().addWidget(QLabel("Param to replace:"))
        self.layout().addWidget(self.param_input)
        self.layout().addWidget(QLabel("Values (one per line):"))
        self.layout().addWidget(self.values_input)
        self.layout().addWidget(self.send_btn)
        self.layout().addWidget(self.results_table)

    def send_bulk(self):
        template = self.req_editor.toPlainText()
        param = self.param_input.text()
        values = [line.strip() for line in self.values_input.toPlainText().split('\n') if line.strip()]
        self.results_table.setRowCount(0)
        for value in values:
            req_text = template.replace(f"{{{param}}}", value)
            try:
                lines = [l for l in req_text.split('\n') if l.strip()]
                method, url = lines[0].split()[:2]
                headers = {}
                body = None
                for line in lines[1:]:
                    if ':' in line:
                        k, v = line.split(':', 1)
                        headers[k.strip()] = v.strip()
                    elif line:
                        body = line
                resp = requests.request(method, url, headers=headers, data=body, verify=False)
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                self.results_table.setItem(row, 0, QTableWidgetItem(value))
                self.results_table.setItem(row, 1, QTableWidgetItem(str(resp.status_code)))
                self.results_table.setItem(row, 2, QTableWidgetItem(str(len(resp.content))))
            except Exception as ex:
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                self.results_table.setItem(row, 0, QTableWidgetItem(value))
                self.results_table.setItem(row, 1, QTableWidgetItem("ERR"))
                self.results_table.setItem(row, 2, QTableWidgetItem(str(ex)))
