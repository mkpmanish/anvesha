# utils.py
def parse_request(req_text):
    lines = req_text.strip().split('\n')
    method, url = lines[0].split()[:2]
    headers = {}
    body = ''
    body_started = False
    for line in lines[1:]:
        if not body_started and ':' in line:
            k, v = line.split(':', 1)
            headers[k.strip()] = v.strip()
        elif line:
            body_started = True
            body += line + '\n'
    return method, url, headers, body.strip()
