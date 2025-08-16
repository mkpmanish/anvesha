# main.py

import sys
import os
import json
import threading
import socket
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QFileDialog
)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from logger_widget import LoggerWidget
from replay_widget import ReplayWidget
from bulksender_widget import BulkSenderWidget
from proxy_runner import ProxyRunner
import webbrowser
from urllib.parse import urlparse

SOCKET_PATH = "/tmp/anvesha_proxy.sock"  # Adjust if needed for your OS


class FlowEventEmitter(QObject):
    new_flow = pyqtSignal(dict)


class FlowReceiverThread(threading.Thread):
    def __init__(self, emit_flow_callback):
        super().__init__(daemon=True)
        self.emit_flow_callback = emit_flow_callback
        self._running = True
        # Remove socket file before binding
        try:
            if os.path.exists(SOCKET_PATH):
                os.unlink(SOCKET_PATH)
        except Exception:
            pass

        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(SOCKET_PATH)
        self.server.listen(1)

    def run(self):
        while self._running:
            try:
                conn, _ = self.server.accept()
                with conn:
                    data = b""
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                    if data:
                        try:
                            for line in data.decode("utf-8").splitlines():
                                flow = json.loads(line)
                                self.emit_flow_callback(flow)
                        except Exception as e:
                            print("Error parsing IPC flow data:", e)
            except Exception as e:
                print("IPC server error:", e)

    def stop(self):
        self._running = False
        self.server.close()
        try:
            os.unlink(SOCKET_PATH)
        except Exception:
            pass


class ProxyConfigWidget(QWidget):
    def __init__(self, start_proxy_callback, stop_proxy_callback, show_cert_callback,
                 get_request_by_id_callback, export_all_callback, import_all_callback):
        super().__init__()
        self.start_proxy_callback = start_proxy_callback
        self.stop_proxy_callback = stop_proxy_callback
        self.show_cert_callback = show_cert_callback
        self.get_request_by_id_callback = get_request_by_id_callback
        self.export_all_callback = export_all_callback
        self.import_all_callback = import_all_callback

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
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Proxy")
        self.stop_button.clicked.connect(self.on_stop_proxy)
        layout.addWidget(self.stop_button)

        self.cert_button = QPushButton("Show mitmproxy CA Cert Location")
        self.cert_button.clicked.connect(self.show_cert_callback)
        layout.addWidget(self.cert_button)

        # --- OpenAPI Export Controls ---
        export_layout = QHBoxLayout()
        export_label = QLabel("Request ID to Export:")
        self.export_id_input = QLineEdit()
        self.export_id_input.setPlaceholderText("Request ID UUID")
        export_btn = QPushButton("Export as OpenAPI 3.0 JSON")
        export_btn.clicked.connect(self.export_openapi)

        export_layout.addWidget(export_label)
        export_layout.addWidget(self.export_id_input)
        export_layout.addWidget(export_btn)
        layout.addLayout(export_layout)

        # --- Import/Export All Controls ---
        imp_exp_layout = QHBoxLayout()
        export_all_btn = QPushButton("Export All (Logger & Replay)")
        import_all_btn = QPushButton("Import All")

        export_all_btn.clicked.connect(self.export_all)
        import_all_btn.clicked.connect(self.import_all)

        imp_exp_layout.addWidget(export_all_btn)
        imp_exp_layout.addWidget(import_all_btn)
        layout.addLayout(imp_exp_layout)

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
            self.status_label.setText(f"Starting proxy on {host}:{port}...")
        except Exception as ex:
            self.status_label.setText(f"Failed to start proxy: {str(ex)}")

    def on_stop_proxy(self):
        self.stop_proxy_callback()
        self.status_label.setText("Stopping proxy...")

    def export_openapi(self):
        req_id = self.export_id_input.text().strip()
        if not req_id:
            QMessageBox.warning(self, "Input Error", "Enter a valid Request ID.")
            return
        req_dict = self.get_request_by_id_callback(req_id)
        if not req_dict:
            QMessageBox.warning(self, "Error", f"No request found with ID {req_id}.")
            return

        operation = openapi_from_request(req_dict)
        openapi_spec = build_basic_openapi_document(operation)
        openapi_json = json.dumps(openapi_spec, indent=2)

        dlg = QMessageBox(self)
        dlg.setWindowTitle("Exported OpenAPI 3.0")
        dlg.setText("OpenAPI 3.0 JSON exported. Save to file as needed.")
        dlg.setDetailedText(openapi_json)
        dlg.exec_()

    def export_all(self):
        if self.export_all_callback:
            self.export_all_callback()

    def import_all(self):
        if self.import_all_callback:
            self.import_all_callback()


def openapi_from_request(req_dict):
    method = req_dict.get("method", "get").lower()
    url = req_dict.get("url", "")
    parsed = urlparse(url)
    path = parsed.path or "/"
    params = []
    if parsed.query:
        for part in parsed.query.split('&'):
            if '=' in part:
                k, v = part.split('=', 1)
            else:
                k, v = part, ""
            params.append({
                "name": k,
                "in": "query",
                "required": False,
                "schema": {"type": "string"},
                "example": v
            })
    headers = req_dict.get("headers", {})
    request_body = None
    if req_dict.get("body"):
        request_body = {
            "content": {
                "application/json": {
                    "example": req_dict["body"]
                }
            }
        }
    op = {
        path: {
            method: {
                "summary": f"{method.upper()} {path}",
                "parameters": params + [
                    {
                        "name": k,
                        "in": "header",
                        "required": False,
                        "schema": {"type": "string"},
                        "example": v
                    } for k, v in headers.items()
                ],
                "requestBody": request_body,
                "responses": {
                    "default": {
                        "description": "default response"
                    }
                }
            }
        }
    }
    return op


def build_basic_openapi_document(operation):
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Exported API",
            "version": "1.0.0"
        },
        "paths": operation
    }


def make_req_str_from_dict(req_dict):
    request_line = f"{req_dict.get('method', '')} {req_dict.get('url', '')}"
    request_line = f"{req_dict.get('method', '')} {req_dict.get('url', '')}"
    headers = req_dict.get('headers', {})
    headers_str = "\n".join(f"{k}: {v}" for k, v in headers.items()) if headers else ""
    body = req_dict.get('body', '')
    parts = [request_line]
    if headers_str:
        parts.append(headers_str)
    if body:
        parts.append("")
        parts.append(body)
    return "\n".join(parts)


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anvesha - Web Security Proxy")
        self.resize(1400, 900)

        self.tabs = QTabWidget()
        self.logger_tab = LoggerWidget(self.send_to_replay, self.send_to_bulk_sender)
        self.replay_tab = ReplayWidget()
        self.bulk_tab = BulkSenderWidget()

        self.proxy_runner = ProxyRunner()
        self.proxy_tab = ProxyConfigWidget(
            self.start_proxy,
            self.stop_proxy,
            self.show_cert,
            self.get_request_by_id,
            self.export_all_data,
            self.import_all_data,
        )

        self.tabs.addTab(self.proxy_tab, "Proxy Config")
        self.tabs.addTab(self.logger_tab, "Request Logger")
        self.tabs.addTab(self.replay_tab, "Replay")
        self.tabs.addTab(self.bulk_tab, "Bulk Sender")

        self.setCentralWidget(self.tabs)

        self.flow_emitter = FlowEventEmitter()
        self.flow_emitter.new_flow.connect(self._on_new_flow)
        self.flow_receiver = FlowReceiverThread(self.flow_emitter.new_flow.emit)
        self.flow_receiver.start()

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_proxy_status)
        self.status_timer.start(2000)  # every 2 seconds

        self.request_map = {}

    def update_proxy_status(self):
        if self.proxy_runner.is_running():
            self.proxy_tab.status_label.setText("Proxy is running")
        else:
            self.proxy_tab.status_label.setText("Proxy is stopped")

    def _on_new_flow(self, flow):
        req_dict = {
            "id": flow.get("id"),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "method": flow.get("method", ""),
            "url": flow.get("url", ""),
            "headers": flow.get("headers", {}),
            "body": flow.get("body", ""),
        }
        resp_dict = {
            "status": flow.get("response_status", ""),
            "headers": flow.get("response_headers", {}),
            "body": flow.get("response_body", ""),
        }
        self.request_map[req_dict["id"]] = req_dict
        self.logger_tab.log_request(req_dict, resp_dict)

    def start_proxy(self, host, port):
        self.proxy_runner.start_proxy(host, port)

    def stop_proxy(self):
        self.proxy_runner.stop_proxy()

    def show_cert(self):
        home = os.path.expanduser("~")
        mitmproxy_dir = os.path.join(home, ".mitmproxy")
        ca_cert_file = os.path.join(mitmproxy_dir, "mitmproxy-ca-cert.pem")
        msg = (
            f"The mitmproxy CA cert is located at:\n\n{ca_cert_file}\n\n"
            "Import it into your browser or device to intercept HTTPS traffic. "
            "Visit http://mitm.it while the proxy is running for "
            "browser-specific installation instructions."
        )
        QMessageBox.information(self, "mitmproxy CA Certificate Location", msg)
        if os.path.exists(mitmproxy_dir):
            webbrowser.open(f"file://{mitmproxy_dir}")

    def send_to_replay(self, req_text=None):
        if req_text is None:
            row = self.logger_tab.table.currentRow()
            if row == -1:
                return
            req_item = self.logger_tab.table.item(row, 2)
            if req_item:
                req_text = req_item.text()
        if req_text:
            self.replay_tab.add_new_tab(req_text)

    def send_to_bulk_sender(self, req_text=None):
        if req_text is None:
            row = self.logger_tab.table.currentRow()
            if row == -1:
                return
            req_item = self.logger_tab.table.item(row, 2)
            if req_item:
                req_text = req_item.text()
        if req_text:
            self.bulk_tab.add_request(req_text)

    def get_request_by_id(self, req_id):
        return self.request_map.get(req_id)

    def export_all_data(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Exported Data", "", "JSON Files (*.json)")
        if not filename:
            return
        try:
            # Prepare clean dict format for logger requests
            logger_data = []
            for req_id, timestamp, req_str, resp_str in self.logger_tab.all_rows:
                req_dict = self.logger_tab.parse_req_resp_to_dict(req_id, timestamp, req_str)
                resp_dict = self.logger_tab.parse_resp_str_to_dict(resp_str)
                logger_data.append({'request': req_dict, 'response': resp_dict})

            replay_data = self.replay_tab.get_all_replay_data()

            data = {
                "logger_requests": logger_data,
                "replay_requests": replay_data
            }

            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
            QMessageBox.information(self, "Export Successful", f"Exported data saved to {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))

    def make_req_str_from_dict(req_dict):
        """Helper to build a request string from parsed dict."""
        request_line = f"{req_dict.get('method', '')} {req_dict.get('url', '')}"
        headers = req_dict.get('headers', {})
        headers_str = "\n".join(f"{k}: {v}" for k, v in headers.items()) if headers else ""
        body = req_dict.get('body', '')
        parts = [request_line]
        if headers_str:
            parts.append(headers_str)
        if body:
            parts.append("")  # blank line before body
            parts.append(body)
        return "\n".join(parts)

    def import_all_data(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Exported Data", "", "JSON Files (*.json)")
        if not filename:
            return
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            logger_requests = data.get("logger_requests", [])
            replay_requests = data.get("replay_requests", [])

            self.logger_tab.clear_all()
            for item in logger_requests:
                req_dict = item.get('request', {})
                print(req_dict)
                resp_dict = item.get('response', {})
                if req_dict:
                    self.logger_tab.log_request(req_dict, resp_dict)

            self.replay_tab.clear_all()
            for item in replay_requests:
                self.replay_tab.load_replay_data(item)

            QMessageBox.information(self, "Import Successful", f"Imported data loaded from {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Import Failed", str(e))


    def closeEvent(self, event):
        self.flow_receiver.stop()
        self.proxy_runner.stop_proxy()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
