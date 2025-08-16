# replay_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QTabWidget


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

    def load_request(self, req_text):
        self.req_editor.setPlainText(req_text)
        self.res_display.clear()

    def send_request(self):
        req_text = self.req_editor.toPlainText()
        try:
            lines = [l for l in req_text.strip().split('\n') if l.strip()]
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
        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_count = 0

    def add_new_tab(self, req_text):
        self.tab_count += 1
        new_tab = SingleReplayTab()
        new_tab.load_request(req_text)
        self.tab_widget.addTab(new_tab, str(self.tab_count))
        self.tab_widget.setCurrentWidget(new_tab)
