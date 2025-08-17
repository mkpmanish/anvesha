# replay_widget.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QTabWidget,
    QHBoxLayout, QFileDialog, QMessageBox, QLineEdit, QApplication
)
from PyQt5.QtCore import QDateTime


def get_main_window_with_tabs(widget):
    parent = widget.parent()
    while parent is not None:
        if hasattr(parent, "tabs"):
            return parent
        parent = parent.parent()
    return None


class SingleReplayTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.req_editor = QTextEdit()
        self.res_display = QTextEdit()
        self.res_display.setReadOnly(True)

        layout.addWidget(QLabel("Request:"))
        layout.addWidget(self.req_editor)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_request)
        layout.addWidget(send_btn)

        layout.addWidget(QLabel("Response:"))
        layout.addWidget(self.res_display)

    def load_data(self, data):
        self.req_editor.setPlainText(data.get('request', ''))
        self.res_display.setPlainText(data.get('response', ''))

    def get_data(self):
        return {
            'request': self.req_editor.toPlainText(),
            'response': self.res_display.toPlainText()
        }

    def send_request(self):
        req_text = self.req_editor.toPlainText()
        try:
            # lines = [l for l in req_text.strip().split('\n') if l.strip()]
            lines = req_text.splitlines()
            request_line = lines[0]
            method, url, *_ = request_line.split()
            headers = {}
            body_lines = []
            is_body = False
            for line in lines[1:]:
                if not is_body and ':' in line:
                    k, v = line.split(':', 1)
                    headers[k.strip()] = v.strip()
                elif line == '':
                    is_body = True
                else:
                    is_body = True
                    body_lines.append(line)
            body = '\n'.join(body_lines) if body_lines else None

            from urllib.parse import urlparse
            parsed = urlparse(url)
            if not parsed.scheme:
                self.res_display.setPlainText("Error: URL must be absolute (include http:// or https://)")
                return

            import requests
            resp = requests.request(
                method,
                url,
                headers=headers,
                data=body,
                verify=False,
                timeout=20
            )
            resp_txt = f"{resp.status_code} {resp.reason}\n"
            resp_txt += "\n".join(f"{k}: {v}" for k, v in resp.headers.items())
            resp_txt += "\n\n" + resp.text
            self.res_display.setPlainText(resp_txt)
        except Exception as ex:
            self.res_display.setPlainText(f"Error parsing or sending request:\n{str(ex)}")


class ReplayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.screenshot_folder = ""

        self.layout = QVBoxLayout(self)

        # Screenshot / Folder Selection layout (if you have this section - keep it as is)
        shot_layout = QHBoxLayout()
        self.folder_label = QLabel("Screenshot folder:")
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        select_btn = QPushButton("Select Folder")
        select_btn.clicked.connect(self.select_folder)
        save_shot_btn = QPushButton("Save Screenshot")
        save_shot_btn.clicked.connect(self.save_screenshot)

        shot_layout.addWidget(self.folder_label)
        shot_layout.addWidget(self.folder_edit)
        shot_layout.addWidget(select_btn)
        shot_layout.addWidget(save_shot_btn)
        self.layout.addLayout(shot_layout)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Add Send to Bulk Sender button below tabs
        self.send_to_bulk_btn = QPushButton("Send Selected Tab to Bulk Sender")
        self.send_to_bulk_btn.clicked.connect(self.send_selected_to_bulk_sender)
        self.layout.addWidget(self.send_to_bulk_btn)

        self.tab_count = 0

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Screenshot Folder")
        if folder:
            self.screenshot_folder = folder
            self.folder_edit.setText(folder)

    def save_screenshot(self):
        if not self.screenshot_folder:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder to save screenshots.")
            return
        win = self.window()
        pix = win.grab()
        ts = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
        fname = os.path.join(self.screenshot_folder, f"screenshot_{ts}.png")
        pix.save(fname)
        QMessageBox.information(self, "Screenshot Saved", f"Screenshot saved at:\n{fname}")

    def send_selected_to_bulk_sender(self):
        current_tab = self.tab_widget.currentWidget()
        if not current_tab:
            QMessageBox.information(self, "No Tab Selected", "No replay tab is currently selected.")
            return
        req_text = current_tab.req_editor.toPlainText()
        if not req_text.strip():
            QMessageBox.warning(self, "Empty Request", "The selected replay tab has an empty request.")
            return

        main_win = get_main_window_with_tabs(self)
        bulk_tab = None
        if main_win:
            for i in range(main_win.tabs.count()):
                widget = main_win.tabs.widget(i)
                if widget and widget.__class__.__name__ == 'BulkSenderWidget':
                    bulk_tab = widget
                    break

        if not bulk_tab:
            QMessageBox.warning(self, "Bulk Sender Tab Not Found", "Could not find Bulk Sender tab to send requests.")
            return

        bulk_tab.add_request(req_text)
        index = main_win.tabs.indexOf(bulk_tab)
        if index != -1:
            main_win.tabs.setCurrentIndex(index)

    def add_new_tab(self, req_text, resp_text=""):
        self.tab_count += 1
        new_tab = SingleReplayTab()
        new_tab.load_data({'request': req_text, 'response': resp_text})
        self.tab_widget.addTab(new_tab, str(self.tab_count))
        self.tab_widget.setCurrentWidget(new_tab)

    def get_all_replay_data(self):
        data = []
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            data.append(tab.get_data())
        return data

    def clear_all(self):
        self.tab_widget.clear()

    def load_replay_data(self, data):
        self.add_new_tab(data.get('request', ''), data.get('response', ''))
