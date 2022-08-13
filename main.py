import requests

import district
import ua_pool
import random
import time
from bs4 import BeautifulSoup


class LianJiaSpider:

    def __init__(self):
        self.url = 'https://xa.ke.com/ershoufang/{}/pg{}ba{}ea{}'
        # 每页条数
        self.page_size = 30
        # 请求重试次数
        self.retry = 10

    # 计算总页数
    def get_total_page_num(self, total_count: int):
        return (total_count + self.page_size - 1) // self.page_size

    # 发起请求
    def load_data(self, key: str, page_num: int, area: int, limit: int):
        url = self.url.format(key, page_num, area, area + limit)
        retry = 1
        while retry <= self.retry:
            try:
                header = {
                    'User-Agent': random.choice(ua_pool.ua_info_list)
                }
                return requests.get(url=url, headers=header)
            except Exception as e:
                print('第{}次请求{}出现异常，开始重试'.format(retry, url), e)
                retry += 1
                time.sleep(3)

    # 执行爬虫
    def run(self):
        # 初始化ua池
        ua_pool.init()

        # 遍历区域选项
        district_map = district.district_map
        for key, value in district_map.items():
            area = 0
            limit = 10
            while area < 10000:
                if 90 <= area < 150:
                    limit = 5
                elif 150 <= area < 200:
                    limit = 10
                elif area >= 200:
                    limit = 10000

                total_page_num = 100
                page_num = 1
                while page_num <= total_page_num:
                    # 发起请求
                    request = self.load_data(key, page_num, area, limit)
                    if request is not None:
                        # 解析html
                        soup = BeautifulSoup(request.text, 'lxml')
                        house_list = soup.find_all('li', class_='clear')
                        if len(house_list) == 0:
                            break

                        for info in house_list:
                            title = info.find('div', class_='title').text.replace('\n', '')
                            position_info = info.find('div', class_='positionInfo').text.replace('\n', '')
                            house_info_list = info.find('div', class_='houseInfo').text.replace('\n', '').split()
                            print(title + position_info)

                        # 处理分页
                        if page_num == 1:
                            total_count = soup.find('h2', class_='total fl').find('span').string
                            if int(total_count) > 3000:
                                raise ValueError('超过3000个结果集，url：{}'.format(request.url))
                            total_page_num = self.get_total_page_num(int(total_count))
                    page_num += 1
                area += limit


if __name__ == '__main__':
    spider = LianJiaSpider()
    spider.run()
