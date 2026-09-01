import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
}

BASE_URL = "https://movie.douban.com/top250"

def get_page_html(url):
    """发送请求获取页面HTML"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status() 
        response.encoding = 'utf-8'
        return response.text
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None

def parse_movie_item(movie_item):
    """解析单个电影条目，提取信息"""
    movie_info = {}
    
    title = movie_item.find('span', class_='title')
    movie_info['title'] = title.text.strip() if title else 'N/A'
    
    other_title = movie_item.find('span', class_='other')
    movie_info['other_title'] = other_title.text.strip() if other_title else ''
    
    link = movie_item.find('div', class_='hd').find('a')
    movie_info['detail_url'] = link.get('href') if link else ''
    
    rating = movie_item.find('span', class_='rating_num')
    movie_info['rating'] = rating.text.strip() if rating else '0'
    
    star = movie_item.find('div', class_='star')
    if star:
        rating_people = star.find_all('span')[-1].text
        movie_info['rating_people'] = re.findall(r'\d+', rating_people)[0]
    else:
        movie_info['rating_people'] = '0'
    
    bd = movie_item.find('div', class_='bd')
    if bd:
        p = bd.find('p')
        if p:
            p_text = p.text.strip().split('\n')
            if len(p_text) > 0:
                director_actor = p_text[0].strip()
                director_match = re.search(r'导演:(.*?)(?:主演:|$)', director_actor)
                movie_info['director'] = director_match.group(1).strip() if director_match else ''
                actor_match = re.search(r'主演:(.*?)$', director_actor)
                movie_info['actors'] = actor_match.group(1).strip() if actor_match else ''
            
            if len(p_text) > 1:
                year_area = p_text[1].strip().split('/')
                movie_info['year'] = year_area[0].strip() if len(year_area) > 0 else ''
                movie_info['area'] = year_area[1].strip() if len(year_area) > 1 else ''
                movie_info['genre'] = year_area[2].strip() if len(year_area) > 2 else ''
    
    quote = movie_item.find('span', class_='inq')
    movie_info['quote'] = quote.text.strip() if quote else ''
    
    return movie_info

def crawl_douban_top250():
    """主爬虫函数"""
    all_movies = []
    
    for page in range(0, 250, 25): 
        url = f"{BASE_URL}?start={page}&filter="
        print(f"正在爬取第 {page//25 + 1} 页: {url}")
        
        html = get_page_html(url)
        if not html:
            print(f"第 {page//25 + 1} 页爬取失败")
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        movie_items = soup.find_all('div', class_='item')
        
        for item in movie_items:
            movie_info = parse_movie_item(item)
            all_movies.append(movie_info)
            print(f"已获取: {movie_info['title']} - 评分: {movie_info['rating']}")
        
        time.sleep(random.uniform(1, 3))
    
    return all_movies

def save_to_csv(movies, filename='douban_top250.csv'):
    """保存数据到CSV文件"""
    if not movies:
        print("没有数据可保存")
        return
    
    keys = ['title', 'other_title', 'director', 'actors', 'year', 
            'area', 'genre', 'rating', 'rating_people', 'quote', 'detail_url']
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(movies)
    
    print(f"\n数据已保存到 {filename}，共 {len(movies)} 条记录")

def main():
    """主函数"""
    print("开始爬取豆瓣电影Top250...")
    movies = crawl_douban_top250()
    save_to_csv(movies)
    print("爬取完成！")

if __name__ == "__main__":
    main()