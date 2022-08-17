import datetime
import re
import time
from decimal import *

import pymysql
import requests
from bs4 import BeautifulSoup

import district
import proxy_pool
import ua_pool


class BeiKeSpider:

    def __init__(self):
        self.url = 'https://xa.ke.com/ershoufang/{}/pg{}ba{}ea{}'
        # 每页条数
        self.page_size = 30
        # 请求重试次数
        self.retry = 10
        # 总插入条数
        self.total_insert = 0
        # 数据库
        self.db = pymysql.connect(host='192.168.0.119', user='ingage', password='ingage', database='dijia478_test')
        # 脚本执行时间
        self.datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 计算总页数
    def get_total_page_num(self, total_count: int):
        return (total_count + self.page_size - 1) // self.page_size

    # 发起请求
    def load_data(self, key: str, page_num: int, area: int, limit: int):
        url = self.url.format(key, page_num, area, area + limit)
        retry = 1
        while retry <= self.retry:
            try:
                time.sleep(1)
                header = {
                    'User-Agent': ua_pool.get_ua()
                }
                proxy = proxy_pool.get_proxies()
                return requests.get(url=url, headers=header, proxies=proxy, timeout=3)
            except:
                print('{} 第{}次请求{}出现异常，稍后开始重试'.format(datetime.datetime.now(), retry, url))
                retry += 1
                time.sleep(30)

    # 批量插入数据库
    def insert_data(self, data_list):
        cursor = spider.db.cursor()
        sql = 'insert into `second_hand_house`(`project_name`,`district`,`house_type`,`build_date`,`release_date`,`follower_num`,`buy_area`,`floor_num`,`total_floor_num`,`unit_price`,`total_price`,`create_time`,`update_time`) values (%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s)'
        try:
            # 执行sql语句
            cursor.executemany(sql, data_list)
            # 将数据提交数据库
            self.db.commit()
            self.total_insert += len(data_list)
            print('{} 本次插入数据库：{}条数据，共：{}条\n'.format(datetime.datetime.now(), len(data_list), self.total_insert))
        except Exception as e:
            print('批量插入数据库发生错误，开始回滚', e)
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
            print('{} 查询{}的房源'.format(datetime.datetime.now(), value))
            area = 0  # 面积
            limit = 10  # 面积步长
            while area < 10000:
                if 90 <= area < 150:
                    limit = 5
                elif 150 <= area < 200:
                    limit = 10
                elif area >= 200:
                    limit = 10000

                print('{} 面积区间{}到{}的房源：'.format(datetime.datetime.now(), area, area + limit))
                data_list = []  # 本次要批量插入的数据
                total_page_num = 100  # 总页数
                page_num = 1  # 当前页数
                while page_num <= total_page_num:
                    # 发起请求
                    response = self.load_data(key, page_num, area, limit)
                    if response is not None:
                        # 解析html
                        soup = BeautifulSoup(response.text, 'lxml')
                        house_list = soup.find_all('li', class_='clear')
                        if len(house_list) == 0 and page_num != 1:
                            print("{} 当前页面 {} 没数据，重新请求".format(datetime.datetime.now(), self.url.format(key, page_num, area, area + limit)))
                            time.sleep(30)
                            continue

                        for info in house_list:
                            title_list = info.find('div', class_='title').text.replace('\n', '').split()
                            house_info_list = info.find('div', class_='houseInfo').text.replace('\n', '').split()
                            follow_info_list = info.find('div', class_='followInfo').text.replace('\n', '').split('/')
                            unit_price = info.find('div', class_='unitPrice').text.replace('\n', '').replace(',', '')
                            unit_price = Decimal(re.search(r'\d+', unit_price).group())
                            info_dict = {}
                            for house_info in house_info_list:
                                if '室' in house_info and '厅' in house_info:
                                    info_dict['house_type'] = house_info
                                elif '年建' in house_info:
                                    info_dict['build_date'] = house_info.strip('建')
                                elif '平米' in house_info:
                                    info_dict['buy_area'] = Decimal(house_info.strip('平米'))
                                    info_dict['total_price'] = info_dict['buy_area'] * unit_price
                                elif '楼层' in house_info and '地下' in house_info:
                                    info_dict['floor_num'] = house_info
                                elif '共' in house_info and '层' in house_info:
                                    info_dict['total_floor_num'] = re.search(r'\d+', house_info).group()
                            for follow_info in follow_info_list:
                                if '关注' in follow_info:
                                    info_dict['follower_num'] = re.search(r'\d+', follow_info).group()
                                elif '发布' in follow_info:
                                    info_dict['release_date'] = follow_info.strip().replace('发布', '')
                            data = (title_list[0], value, info_dict.get('house_type'), info_dict.get('build_date'),
                                    info_dict.get('release_date'), info_dict.get('follower_num'),
                                    info_dict.get('buy_area'), info_dict.get('floor_num'),
                                    info_dict.get('total_floor_num'), unit_price, info_dict.get('total_price'),
                                    self.datetime, self.datetime)
                            data_list.append(data)

                        # 处理分页
                        if page_num == 1:
                            total_count = soup.find('h2', class_='total fl').find('span').string
                            if int(total_count) > 3000:
                                raise ValueError('超过3000个结果集，url：{}'.format(response.url))
                            total_page_num = self.get_total_page_num(int(total_count))
                    else:
                        print('{} 重试10次依然失败，跳过当前界面。。。'.format(datetime.datetime.now()))
                    page_num += 1

                # 批量插入
                self.insert_data(data_list)
                area += limit


if __name__ == '__main__':
    print('爬取开始', datetime.datetime.now())
    spider = BeiKeSpider()
    spider.run()
    # 关闭数据库连接
    spider.db.close()
    print('爬取结束', datetime.datetime.now())
