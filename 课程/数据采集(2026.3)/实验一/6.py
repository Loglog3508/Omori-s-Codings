import requests
import re

print("\n" + "="*50)
print("6. 抓取豆瓣电影TOP250评分")
print("="*50)

url = 'https://movie.douban.com/top250'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = 'utf-8'
    html = response.text

    pattern = r'<span class="title">([^<]+)</span>.*?<span class="rating_num" property="v:average">([\d.]+)</span>'
    movies = re.findall(pattern, html, re.S)

    print(f"成功抓取 {len(movies)} 部电影：")
    for i, (title, rating) in enumerate(movies[:10], 1):
        print(f"{i}. {title} —— 评分：{rating}")

except Exception as e:
    print(f"失败: {e}")