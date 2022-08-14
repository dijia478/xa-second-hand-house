import requests
import random
from bs4 import BeautifulSoup

import ua_pool

ip_proxy_pool = [
    {'http': 'http://101.200.127.149:3129', 'https': 'http://101.200.127.149:3129'}
]


def init():
    url = 'http://www.66ip.cn/{}.html'
    for i in range(2000):
        response = requests.get(url=url.format(i + 1))
        response.encoding = 'gb2312'
        soup = BeautifulSoup(response.text, 'lxml')
        find_all = soup.find_all('tr')
        for ip_port in find_all:
            if '全国代理' in ip_port.find_all('td')[0].text or 'ip' in ip_port.find_all('td')[0].text:
                continue
            ip = ip_port.find_all('td')[0].text
            port = ip_port.find_all('td')[1].text
            check_ip(ip, port)
        if len(ip_proxy_pool) > 10:
            break
    print('代理池初始化完成', len(ip_proxy_pool))


def check_ip(ip: str, port: str):
    headers = {
        'User-Agent': ua_pool.get_ua()
    }
    proxies = {
        "http": 'http://' + ip + ':' + port,
        "https": 'http://' + ip + ':' + port
    }
    try:
        response = requests.get(url='https://xa.ke.com/ershoufang/', headers=headers, proxies=proxies, timeout=5)  # 设置timeout，使响应等待1s
        if response.status_code == 200:
            print(proxies, '可用')
            ip_proxy_pool.append(proxies)
        else:
            print(proxies, '不可用')
    except Exception as e:
        print(proxies, '请求异常', e)


def get_proxies():
    if not ip_proxy_pool:
        init()
    return random.choice(ip_proxy_pool)


if __name__ == '__main__':
    init()
    file_path = 'ip_proxy_pool.txt'
    with open(file_path, mode='w', encoding='utf-8') as file_obj:
        file_obj.write(str(ip_proxy_pool))