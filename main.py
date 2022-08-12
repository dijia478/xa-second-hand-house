import requests

import district
import ua_pool
import random
from bs4 import BeautifulSoup


# 计算总页数
def get_total_page_num(total_count: int, page_size: int):
    return (total_count + page_size - 1) // page_size


# 发起请求
def load_data(key: str, page_num: int):
    url = 'https://xa.ke.com/ershoufang/' + key + '/pg' + str(page_num) + '/'
    header = {
        'User-Agent': random.choice(ua_pool.ua_info_list)
    }
    return requests.get(url=url, headers=header)


# 执行爬虫
def run():
    # 初始化ua池
    ua_pool.init()

    # 遍历区域选项
    district_map = district.district_map
    for key, value in district_map.items():
        total_page_num = 100
        page_num = 1
        while page_num <= total_page_num:
            # 发起请求
            request = load_data(key, page_num)

            # 解析html
            soup = BeautifulSoup(request.text, 'lxml')
            house_list = soup.find_all('li', class_='clear')
            for house_info in house_list:
                title = house_info.find('div', class_='title').find('a').string
                position_info = house_info.find('div', class_='positionInfo').find('a').string
                print(title + position_info)

            # 处理分页
            if page_num == 1:
                total_count = soup.find('h2', class_='total fl').find('span').string
                total_page_num = get_total_page_num(int(total_count), 30)
            page_num += 1


if __name__ == '__main__':
    run()
