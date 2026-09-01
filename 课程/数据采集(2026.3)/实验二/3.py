import requests
from lxml import html
import csv
import time
import random

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def get_movies(url):
    resp = requests.get(url, headers=HEADERS)
    tree = html.fromstring(resp.text)
    
    movies = []
    for item in tree.xpath('//div[@class="item"]'):
        movie = {
            'title': item.xpath('.//span[@class="title"]/text()')[0],
            'rating': item.xpath('.//span[@class="rating_num"]/text()')[0],
            'quote': item.xpath('.//span[@class="inq"]/text()')[0] if item.xpath('.//span[@class="inq"]/text()') else '',
            'url': item.xpath('.//div[@class="hd"]/a/@href')[0],
        }
        movies.append(movie)
        print(f"{movie['title']} - {movie['rating']}")
    
    return movies

movies = get_movies("https://movie.douban.com/top250?start=0")
print(f"共获取 {len(movies)} 部电影")