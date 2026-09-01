import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8000

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
os.chdir(SRC_DIR)

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"[Server] Request: {self.path}", flush=True)

        if self.path.startswith("/api/proxy"):
            from urllib.parse import urlparse, parse_qs
            import urllib.request
            from urllib.error import HTTPError, URLError

            try:
                query = parse_qs(urlparse(self.path).query)
                target_url = query.get("url", [None])[0]

                if not target_url:
                    self.send_error(400, "Missing url parameter")
                    return

                print(f"[Proxy] Fetching: {target_url}", flush=True)

                if not target_url.startswith(("http://", "https://")):
                    self.send_error(400, "Invalid URL scheme")
                    return

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
                }

                req = urllib.request.Request(target_url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    content = response.read()
                    self.send_response(response.status)
                    ctype = response.headers.get("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-type", ctype)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(content)
                    print(f"[Proxy] Success: {len(content)} bytes", flush=True)

            except HTTPError as e:
                print(f"[Proxy] HTTP Error: {e.code} {e.reason}", flush=True)
                self.send_response(e.code)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                try:
                    self.wfile.write(e.read())
                except:
                    self.wfile.write(str(e).encode("utf-8"))

            except Exception as e:
                print(f"[Proxy] Error: {e}", flush=True)
                self.send_error(500, str(e))
        else:
            super().do_GET()

socketserver.TCPServer.allow_reuse_address = True

try:
    with socketserver.ThreadingTCPServer(("", PORT), ProxyHandler) as httpd:
        print(f"DeepVision Server Starting...")
        print(f"Address: http://localhost:{PORT}")
        print(f"Opening browser...")
        webbrowser.open(f"http://localhost:{PORT}/index.html")
        print("Server running... Press Ctrl+C to stop")
        httpd.serve_forever()
except OSError as e:
    if e.errno == 98 or e.errno == 10048:
        print(f"Port {PORT} in use, trying 8001...")
        PORT = 8001
        with socketserver.ThreadingTCPServer(("", PORT), ProxyHandler) as httpd:
            print(f"Address: http://localhost:{PORT}")
            webbrowser.open(f"http://localhost:{PORT}/index.html")
            httpd.serve_forever()
    else:
        raise e
except KeyboardInterrupt:
    print("\nServer stopped")
