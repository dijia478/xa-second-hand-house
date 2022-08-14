import requests
import random
from bs4 import BeautifulSoup

import ua_pool

ip_proxy_pool = [
    {'http': 'http://95.59.26.129:80', 'https': 'http://95.59.26.129:80'}
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
        if len(ip_proxy_pool) > 20:
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
        response = requests.get(url='http://icanhazip.com', headers=headers, proxies=proxies, timeout=1)  # 设置timeout，使响应等待1s
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
    # for i in range(20):
    #     proxies = get_proxies()
    #     print(proxies)
    proxies = get_proxies()
    req = requests.get('https://icanhazip.com/', proxies=proxies)
    print(req.text)

