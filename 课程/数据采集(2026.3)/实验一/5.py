import requests
import re

print("\n" + "="*50)
print("5. 抓取研究生院网站新闻标题")
print("="*50)

url = 'http://yjs.dep.dlpu.edu.cn/'
try:
    response = requests.get(url, timeout=10)
    response.encoding = response.apparent_encoding
    html = response.text

    pattern = r'<div class="info".*?<a[^>]*title="([^"]+)"'
    titles = re.findall(pattern, html, re.S)

    if not titles:
        pattern2 = r'<div class="info".*?<a[^>]*>(.*?)</a>'
        titles = re.findall(pattern2, html, re.S)
        titles = [re.sub(r'<font.*?>.*?</font>', '', t).strip() for t in titles]

    titles = list(dict.fromkeys(titles))

    if titles:
        print(f"成功抓取到 {len(titles)} 条新闻标题，显示前10条：")
        for idx, title in enumerate(titles[:10], 1):
            print(f"{idx}. {title}")
    else:
        print("未找到新闻标题，请检查网页结构是否变化。")

except Exception as e:
    print(f"发生错误: {e}")