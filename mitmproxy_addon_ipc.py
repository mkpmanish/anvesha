import json
import socket
import os

SOCKET_PATH = "/tmp/anvesha_proxy.sock"
print("==== LOADED mitmproxy_addon_ipc.py ====", flush=True)

def response(flow):
    print("In Addon IPC........")
    data = {
        "id": flow.id,
        "method": flow.request.method,
        "host": flow.request.host,
        "url": flow.request.url,
        "headers": dict(flow.request.headers),
        "body": flow.request.get_text(),
        "response_status": flow.response.status_code if flow.response else None,
        "response_headers": dict(flow.response.headers) if flow.response else None,
        "response_body": flow.response.get_text() if flow.response else None
    }
    print("Trying to send to socket:", SOCKET_PATH)
    try:
        if os.path.exists(SOCKET_PATH):
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.connect(SOCKET_PATH)
                client.sendall((json.dumps(data) + "\n").encode("utf-8"))
            print("Sent flow to socket")
        else:
            print("Socket not found when trying to send.")
    except Exception as e:
        print(f"IPC send error: {e}")
