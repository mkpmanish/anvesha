# proxy_runner.py
import subprocess
import os

class ProxyRunner:
    def __init__(self):
        self.proc = None
        self.flows_file = "anvesha_flows.jsonl"

    def start_proxy(self, host, port):
        if self.proc:
            self.stop_proxy()
        if os.path.exists(self.flows_file):
            os.remove(self.flows_file)
        # Use the exact command, substitute host/port as UI input
        self.proc = subprocess.Popen(
            [
                "mitmdump",
                "-s", "mitmproxy_addon_export_json.py",
                "--listen-host", host,
                "-p", str(port)
            ]
        )

    def stop_proxy(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=5)
            self.proc = None
