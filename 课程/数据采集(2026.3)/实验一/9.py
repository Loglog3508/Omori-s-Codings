import urllib.request
import urllib.parse

print("\n" + "="*50)
print("9. urllib 采集百度首页")
print("="*50)

url = 'http://www.baidu.com'
try:
    response = urllib.request.urlopen(url, timeout=10)
    html = response.read().decode('utf-8')
    print("百度首页内容长度:", len(html))
    print("前200个字符:", html[:200])
except Exception as e:
    print("百度请求失败:", e)

print("\n访问其他网站（httpbin.org/get）:")
url = 'http://httpbin.org/get'
try:
    response = urllib.request.urlopen(url, timeout=10)
    data = response.read().decode('utf-8')
    print("返回数据:", data)
except Exception as e:
    print("请求失败:", e)
