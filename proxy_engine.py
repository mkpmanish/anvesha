# proxy_engine.py
import threading
import asyncio
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from mitmproxy import http

class RequestLoggerAddon:
    def __init__(self, main_app):
        self.main_app = main_app

    def response(self, flow: http.HTTPFlow):
        self.main_app.add_log(flow.request, flow.response)

def _run_proxy(opts, main_app):
    # Each proxy thread gets its own event loop
    asyncio.set_event_loop(asyncio.new_event_loop())
    master = DumpMaster(opts, with_termlog=False, with_dumper=False)
    addon = RequestLoggerAddon(main_app)
    master.addons.add(addon)
    try:
        master.run()
    except KeyboardInterrupt:
        master.shutdown()

def start_proxy(main_app, host, port):
    opts = options.Options(listen_host=host, listen_port=port)
    proxy_thread = threading.Thread(target=_run_proxy, args=(opts, main_app), daemon=True)
    proxy_thread.start()
    return None, proxy_thread
