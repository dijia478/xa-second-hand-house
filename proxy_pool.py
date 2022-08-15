import requests
import random
from bs4 import BeautifulSoup

import ua_pool

ip_proxy_pool = [
]


def init():
    url = 'https://free.kuaidaili.com/free/inha/{}/'
    for i in range(4000):
        header = {
            'User-Agent': ua_pool.get_ua()
        }
        response = requests.get(url=url.format(i + 1), headers=header)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')
        find_all = soup.find_all('tr')
        for ip_port in find_all:
            if 'IP' in ip_port.text:
                continue
            ip = ip_port.find('td', attrs={'data-title': 'IP'}).text
            port = ip_port.find('td', attrs={'data-title': 'PORT'}).text
            check_ip(ip, port)
            if len(ip_proxy_pool) > 5:
                print('代理池初始化完成', len(ip_proxy_pool))
                return


def check_ip(ip: str, port: str):
    proxy = {
        "http": 'http://' + ip + ':' + port,
        "https": 'http://' + ip + ':' + port
    }
    try:
        headers = {
            'User-Agent': ua_pool.get_ua()
        }
        response = requests.get(url='https://xa.ke.com/ershoufang/', headers=headers, proxies=proxy, timeout=5)  # 设置timeout，使响应等待1s
        if response.status_code == 200 and proxy not in ip_proxy_pool:
            print(proxy, '可用')
            ip_proxy_pool.append(proxy)
        else:
            print(proxy, '不可用')
    except:
        print(proxy, '请求异常')


def get_proxies():
    global ip_proxy_pool
    if len(ip_proxy_pool) >= 20:
        return random.choice(ip_proxy_pool)
    with open('ip_proxy_pool.txt', encoding='utf-8') as ip_proxy:
        contents = ip_proxy.read()
        if contents == '':
            init()
        ip_proxy_pool = eval(contents)
        if len(ip_proxy_pool) == 0:
            init()
    return random.choice(ip_proxy_pool)


if __name__ == '__main__':
    print(get_proxies())
    file_path = 'ip_proxy_pool.txt'
    with open(file_path, mode='w', encoding='utf-8') as file_obj:
        file_obj.write(str(ip_proxy_pool))
