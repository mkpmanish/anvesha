import json

def response(flow):
    info = {
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
    with open("anvesha_flows.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(info) + "\n")
