import datetime
import re
import time
import traceback
from decimal import *

import pymysql
import requests
from bs4 import BeautifulSoup

import district
from ua import ua_pool


class RentalSpider:

    def __init__(self):
        self.url = 'https://xa.zu.ke.com/zufang/{}/pg{}rco11brp{}erp{}'
        # 每页条数
        self.page_size = 30
        # 请求重试次数
        self.retry = 20
        # 总插入条数
        self.total_insert = 0
        # 重试异常后等待时间
        self.retry_sleep = 60
        # 数据库
        self.db = pymysql.connect(host='192.168.0.119', user='ingage', password='ingage', database='dijia478_test')
        # 脚本执行时间
        self.datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 设置四舍五入
        getcontext().rounding = "ROUND_HALF_UP"

    # 获取请求租金步长
    @staticmethod
    def get_limit(price):
        if price < 1500:
            return 500
        elif 1500 <= price < 3000:
            return 100
        elif 3000 <= price < 4000:
            return 200
        elif 4000 <= price < 6000:
            return 1000
        elif price >= 6000:
            return 1000000

    # 获取总页数
    def get_total_page_num(self, response, soup, page_num):
        find_p = soup.find('p', class_='content__title')
        if find_p is None:
            return 1000
        find_span = find_p.find('span')
        if find_span is None:
            return 1000
        total_count = find_span.string
        if int(total_count) > 3000:
            print('超过3000个结果集，url：{}'.format(response.url))
            return 100

        total_page_num = (int(total_count) + self.page_size - 1) // self.page_size
        if page_num == 1:
            print('{} 共{}条数据，共{}页'.format(datetime.datetime.now(), total_count, total_page_num))
        return total_page_num

    # 发起请求
    def load_data(self, key: str, page_num: int, price: int, limit: int):
        url = self.url.format(key, page_num, price + 1, price + limit)
        retry = 1
        while retry <= self.retry:
            try:
                time.sleep(1)
                header = {
                    'User-Agent': ua_pool.get_ua()
                }
                # proxy = proxy_pool.get_proxies()
                # return requests.get(url=url, headers=header, proxies=proxy, timeout=3)
                return requests.get(url=url, headers=header, timeout=3)
            except:
                print('{} 第{}次请求 {} 出现异常，稍后开始重试'.format(datetime.datetime.now(), retry, url))
                retry += 1
                time.sleep(self.retry_sleep)

    # 解析网页信息
    def parse_info(self, data_list, house_list, value):
        for info in house_list:
            title_list = info.find('p', class_='content__list--item--title').text.replace('\n', '').split()
            house_info_list = info.find('p', class_='content__list--item--des').text.replace('\n', '').split()
            unit_price = info.find('span', class_='content__list--item-price').text.replace('\n', '')
            unit_price = Decimal(re.search(r'\d+', unit_price).group())
            title = title_list[0]

            info_dict = {}
            if '·' in title:
                info_dict['rental_type'] = title.split('·')[0]
                info_dict['project_name'] = title.split('·')[1]
            else:
                info_dict['project_name'] = title

            for house_info in house_info_list:
                if '室' in house_info and '厅' in house_info:
                    info_dict['house_type'] = house_info.replace('/', '')
                elif '㎡' in house_info:
                    replace = house_info.strip('㎡').replace('/', '')
                    if '-' in replace:
                        info_dict['buy_area'] = Decimal(replace.split('-')[0])
                    else:
                        info_dict['buy_area'] = Decimal(replace)
                elif len(house_info) <= 3 and ('东' in house_info or '南' in house_info or '西' in house_info or '北' in house_info):
                    if 'toward' in info_dict:
                        info_dict['toward'] = info_dict['toward'] + ',' + house_info.replace('/', '')
                    else:
                        info_dict['toward'] = house_info.replace('/', '')

            data = (info_dict.get('project_name'), value, info_dict.get('rental_type'), info_dict.get('toward'),
                    info_dict.get('house_type'), info_dict.get('buy_area'), unit_price,
                    self.datetime, self.datetime)
            data_list.append(data)

    # 批量插入数据库
    def insert_data(self, data_list):
        try:
            if len(data_list) == 0:
                return
            cursor = spider.db.cursor()
            sql = 'insert into `rental_house`(`project_name`,`district`,`rental_type`,`toward`,`house_type`,`buy_area`,`unit_price`,`create_time`,`update_time`) values (%s,%s,%s,%s,%s, %s,%s,%s,%s)'
            # 执行sql语句
            cursor.executemany(sql, data_list)
            # 将数据提交数据库
            self.db.commit()
            self.total_insert += len(data_list)
            print('{} 本次插入数据库：{}条数据，共：{}条\n'.format(datetime.datetime.now(), len(data_list), self.total_insert))
        except Exception as e:
            traceback.print_exc()
            print('{} 批量插入{}条数据发生错误，开始回滚'.format(datetime.datetime.now(), len(data_list)), e)
            # 如果发生错误则回滚
            self.db.rollback()

    # 执行爬虫
    def run(self):
        # 初始化ua池
        ua_pool.init()

        # 遍历区域选项
        district_map = district.district_map
        for key, value in district_map.items():
            print('================================')
            print('{} 查询区域：{}'.format(datetime.datetime.now(), value))
            price = 0  # 租金
            while price < 1000000:
                limit = RentalSpider.get_limit(price)
                print('{} 价格区间{}到{}的房源：'.format(datetime.datetime.now(), price + 1, price + limit))
                data_list = []  # 本次要批量插入的数据
                total_page_num = 100  # 总页数
                page_num = 1  # 当前页数
                while page_num <= total_page_num:
                    try:
                        # 发起请求
                        response = self.load_data(key, page_num, price, limit)
                        if response is not None:
                            # 解析html
                            soup = BeautifulSoup(response.text, 'lxml')
                            # 获取总页数
                            total_page_num = self.get_total_page_num(response, soup, page_num)
                            if total_page_num == 1000 and page_num == 1:
                                print('{} 第一页数据请求失败，无法获取总页数，重新请求'.format(datetime.datetime.now()))
                                time.sleep(self.retry_sleep)
                                continue
                            elif total_page_num == 0 and page_num == 1:
                                print('{} 当前条件下无数据，开始下一个价格段查询，url:{}\n'.format(datetime.datetime.now(), response.url))
                                break

                            content_list = soup.find('div', class_='content__list')
                            if content_list is None:
                                print("{} 当前页面 {} 重定向错误，重新请求".format(datetime.datetime.now(), response.url))
                                time.sleep(self.retry_sleep)
                                continue
                            house_list = content_list.find_all('div', class_='content__list--item')
                            if len(house_list) == 0 and page_num != 1:
                                print("{} 当前页面 {} 重定向错误，重新请求".format(datetime.datetime.now(), response.url))
                                time.sleep(self.retry_sleep)
                                continue

                            # 解析网页信息
                            self.parse_info(data_list, house_list, value)
                        else:
                            print('{} 请求{}次依然失败，跳过当前界面。。。'.format(datetime.datetime.now(), self.retry))
                    except Exception as e:
                        traceback.print_exc()
                        print('发生异常，跳过当前界面，url:{}'.format(self.url.format(key, page_num, price, price + limit)), e)

                    page_num += 1

                # 批量插入
                self.insert_data(data_list)
                price += limit


if __name__ == '__main__':
    spider = RentalSpider()
    print('\n{} 爬取开始'.format(datetime.datetime.now()))
    spider.run()
    # 关闭数据库连接
    spider.db.close()
    print('{} 爬取结束'.format(datetime.datetime.now()))
