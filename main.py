import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import QTimer
from logger_widget import LoggerWidget
from replay_widget import ReplayWidget
from bulksender_widget import BulkSenderWidget
from proxy_runner import ProxyRunner
import webbrowser

class ProxyConfigWidget(QWidget):
    def __init__(self, start_proxy_callback, stop_proxy_callback, show_cert_callback):
        super().__init__()
        self.start_proxy_callback = start_proxy_callback
        self.stop_proxy_callback = stop_proxy_callback
        self.show_cert_callback = show_cert_callback

        layout = QVBoxLayout()
        host_layout = QHBoxLayout()
        host_label = QLabel("Proxy Host:")
        self.host_input = QLineEdit("127.0.0.1")
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host_input)
        layout.addLayout(host_layout)

        port_layout = QHBoxLayout()
        port_label = QLabel("Proxy Port:")
        self.port_input = QLineEdit("8080")
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        layout.addLayout(port_layout)

        self.start_button = QPushButton("Start Proxy")
        self.start_button.clicked.connect(self.on_start_proxy)

        self.stop_button = QPushButton("Stop Proxy")
        self.stop_button.clicked.connect(self.on_stop_proxy)

        self.cert_button = QPushButton("Show mitmproxy CA Cert Location")
        self.cert_button.clicked.connect(self.show_cert_callback)

        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.cert_button)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def on_start_proxy(self):
        host = self.host_input.text().strip()
        port = self.port_input.text().strip()
        if not host or not port.isdigit():
            QMessageBox.warning(self, "Input Error", "Please enter valid host and port.")
            return
        port = int(port)
        try:
            self.start_proxy_callback(host, port)
            self.status_label.setText(f"Proxy running on {host}:{port}")
        except Exception as ex:
            self.status_label.setText(f"Failed to start proxy: {str(ex)}")

    def on_stop_proxy(self):
        self.stop_proxy_callback()
        self.status_label.setText("Proxy stopped.")

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anvesha - Web Security Proxy")
        self.resize(1300, 800)
        self.displayed_flows = set()
        self.last_flow_pos = 0  # track last read position in flows file
        # Initialize displayed_flows before any operation
        self.displayed_flows = set()

        self.tabs = QTabWidget()
        self.logger_tab = LoggerWidget(self.send_to_replay)
        self.replay_tab = ReplayWidget()
        self.bulk_tab = BulkSenderWidget()

        self.proxy_runner = ProxyRunner()
        self.proxy_tab = ProxyConfigWidget(self.start_proxy, self.stop_proxy, self.show_cert)

        self.tabs.addTab(self.proxy_tab, "Proxy Config")
        self.tabs.addTab(self.logger_tab, "Request Logger")
        self.tabs.addTab(self.replay_tab, "Replay")
        self.tabs.addTab(self.bulk_tab, "Bulk Sender")

        self.setCentralWidget(self.tabs)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.parse_flows_file)
        self.timer.start(2000)  # every 2 seconds

    def start_proxy(self, host, port):
        self.proxy_runner.start_proxy(host, port)

    def stop_proxy(self):
        self.proxy_runner.stop_proxy()

    def show_cert(self):
        home = os.path.expanduser('~')
        mitmproxy_dir = os.path.join(home, '.mitmproxy')
        ca_cert_file = os.path.join(mitmproxy_dir, 'mitmproxy-ca-cert.pem')
        msg = (
            f"The mitmproxy CA cert is located at:\n\n{ca_cert_file}\n\n"
            "Import it into your browser or device to intercept HTTPS traffic. "
            "You can also visit http://mitm.it while the proxy is running "
            "for browser-specific installation instructions."
        )
        QMessageBox.information(self, "mitmproxy CA Certificate Location", msg)
        if os.path.exists(mitmproxy_dir):
            webbrowser.open(f'file://{mitmproxy_dir}')

    def parse_flows_file(self):
        flows_file = self.proxy_runner.flows_file
        if not flows_file or not hasattr(self, "logger_tab"):
            return
        if not os.path.exists(flows_file):
            return
        try:
            with open(flows_file, "r", encoding="utf-8") as f:
                # Seek to last read position
                f.seek(self.last_flow_pos)
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        flow = json.loads(line)
                    except Exception as e:
                        print(f"Error parsing flow line: {e}")
                        continue
                    flow_id = flow.get("id")
                    if flow_id and flow_id not in self.displayed_flows:
                        req_dict = {
                            "method": flow.get("method", ""),
                            "url": flow.get("url", ""),
                            "headers": flow.get("headers", {}),
                            "body": flow.get("body", "")
                        }
                        resp_headers = flow.get("response_headers")
                        resp_status = flow.get("response_status")
                        resp_body = flow.get("response_body")
                        resp_dict = None
                        if resp_headers or resp_status or resp_body:
                            resp_dict = {
                                "status": resp_status or "",
                                "headers": resp_headers or {},
                                "body": resp_body or ""
                            }
                        self.logger_tab.log_request(req_dict, resp_dict)
                        self.displayed_flows.add(flow_id)
                # Remember where we ended
                self.last_flow_pos = f.tell()
        except Exception as e:
            print(f"Error reading flows file: {e}")

    def add_log(self, req, res):
        self.logger_tab.log_request(req, res)

    # Inside MainApp class
    def send_to_replay(self, req_text=None):
        if req_text is None:
            row = self.logger_tab.table.currentRow()
            if row == -1:
                return
            req_item = self.logger_tab.table.item(row, 0)
            if req_item:
                req_text = req_item.text()
        if req_text:
            self.replay_tab.add_new_tab(req_text)
            # Do NOT switch tabs if you want to keep the UI on the current tab
            # You can uncomment the next line if you want to switch
            # self.tabs.setCurrentWidget(self.replay_tab)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
