import http.server
import socketserver
import webbrowser
import os
import sys

# 设置端口号
PORT = 8000

# 确保切换到脚本所在的目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

Handler = http.server.SimpleHTTPRequestHandler

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 打印请求路径，确认服务器是否接收到请求
        print(f"[Server] Request: {self.path}", flush=True)
        
        # 简单的 API 代理端点，用于绕过 CORS 限制抓取外部网页 (如百度百科)
        if self.path.startswith('/api/proxy'):
            from urllib.parse import urlparse, parse_qs
            import urllib.request
            from urllib.error import HTTPError, URLError
            
            try:
                query = parse_qs(urlparse(self.path).query)
                target_url = query.get('url', [None])[0]
                
                if not target_url:
                    self.send_error(400, "Missing 'url' parameter")
                    return
                
                print(f"[Proxy] Fetching: {target_url}", flush=True)

                # 简单的安全检查
                if not target_url.startswith(('http://', 'https://')):
                    self.send_error(400, "Invalid URL scheme")
                    return

                # 伪装 User-Agent 防止被反爬，并添加 Accept 头
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
                }
                
                req = urllib.request.Request(target_url, headers=headers)
                # Reduced timeout to 5s to fail faster so client falls back
                with urllib.request.urlopen(req, timeout=5) as response:
                    content = response.read()
                    
                    self.send_response(response.status)
                    # 转发 Content-Type
                    ctype = response.headers.get('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-type', ctype)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(content)
                    print(f"[Proxy] Success: {len(content)} bytes", flush=True)

            except HTTPError as e:
                print(f"[Proxy] HTTP Error: {e.code} {e.reason}", flush=True)
                self.send_response(e.code)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                # 尝试读取错误页面内容
                try:
                    self.wfile.write(e.read())
                except:
                    self.wfile.write(str(e).encode('utf-8'))
                    
            except Exception as e:
                print(f"[Proxy] Error: {e}", flush=True)
                self.send_error(500, str(e))
        else:
            super().do_GET()

# 允许地址重用，防止快速重启时报错
socketserver.TCPServer.allow_reuse_address = True

try:
    # 使用 ThreadingTCPServer 支持并发请求，避免代理请求阻塞主线程
    with socketserver.ThreadingTCPServer(("", PORT), ProxyHandler) as httpd:
        print(f"正在启动本地服务器 (Proxy Enabled)...")
        print(f"服务地址: http://localhost:{PORT}")
        print(f"正在自动打开浏览器...")
        
        # 自动打开默认浏览器访问 education_walkthrough.html
        webbrowser.open(f"http://localhost:{PORT}/index.html")
        
        print("服务器运行中... 请按 Ctrl+C 停止")
        httpd.serve_forever()
except OSError as e:
    if e.errno == 98 or e.errno == 10048: # Address already in use
        print(f"端口 {PORT} 被占用，尝试使用 8001...")
        PORT = 8001
        with socketserver.ThreadingTCPServer(("", PORT), ProxyHandler) as httpd:
            print(f"服务地址: http://localhost:{PORT}")
            webbrowser.open(f"http://localhost:{PORT}/index.html")
            httpd.serve_forever()
            httpd.serve_forever()
    else:
        raise e
except KeyboardInterrupt:
    print("\n服务器已停止")
