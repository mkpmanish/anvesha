import subprocess
import os
import threading

class ProxyRunner:
    def __init__(self):
        self.proc = None

    def start_proxy(self, host, port):
        if self.proc:
            self.stop_proxy()
        addon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mitmproxy_addon_ipc.py"))
        cmd = [
            "mitmdump",
            "-s", addon_path,
            "--listen-host", host,
            "-p", str(port)
        ]
        print("[ProxyRunner] Launching mitmdump:", " ".join(cmd))
        self.proc = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Stream output to the main terminal for debugging
        threading.Thread(target=self._stream_output, args=(self.proc.stdout, 'STDOUT'), daemon=True).start()
        threading.Thread(target=self._stream_output, args=(self.proc.stderr, 'STDERR'), daemon=True).start()
        print(f"[ProxyRunner] mitmdump started with pid {self.proc.pid}")

    def _stream_output(self, pipe, name):
        for line in iter(pipe.readline, b''):
            print(f"[mitmdump {name}] {line.decode('utf-8').rstrip()}")

    def stop_proxy(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=5)
            self.proc = None

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None
