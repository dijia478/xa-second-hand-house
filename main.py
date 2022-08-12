import requests

import district
import ua_pool
import random
from bs4 import BeautifulSoup


# 计算总页数
def get_total_page_num(total_count: int, page_size: int):
    return int((total_count + page_size - 1) / page_size)


# 发起请求
def load_data(key: str, page_num: int):
    url = 'https://xa.ke.com/ershoufang/' + key + '/pg' + str(page_num + 1) + '/'
    header = {
        'User-Agent': random.choice(ua_pool.ua_info_list)
    }
    return requests.get(url=url, headers=header)


# 执行爬虫
def run():
    # 初始化ua池
    ua_pool.init()

    district_map = district.district_map
    for key, value in district_map.items():
        total_page_num = 100
        for page_num in range(total_page_num):
            request = load_data(key, page_num)

            # 解析html
            soup = BeautifulSoup(request.text, 'lxml')
            if page_num == 0:
                total_count = soup.find('h2', class_='total fl').find('span').string
                total_page_num = get_total_page_num(int(total_count), 30)

            house_list = soup.find_all('li', class_='clear')
            for house_info in house_list:
                title = house_info.find('div', class_='title').find('a').string
                position_info = house_info.find('div', class_='positionInfo').find('a').string
                print(title + position_info)


if __name__ == '__main__':
    run()
