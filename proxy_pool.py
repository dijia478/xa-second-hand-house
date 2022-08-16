import requests
import random
from bs4 import BeautifulSoup

import ua_pool

ip_proxy_pool = [
]


def init():
    url = 'https://free.kuaidaili.com/free/inha/{}/'
    for i in range(4000):
        try:
            header = {
                'User-Agent': ua_pool.get_ua()
            }
            response = requests.get(url=url.format(i + 1), headers=header, timeout=3)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
            find_all = soup.find_all('tr')
            for ip_port in find_all:
                if 'IP' in ip_port.text:
                    continue
                ip = ip_port.find('td', attrs={'data-title': 'IP'}).text
                port = ip_port.find('td', attrs={'data-title': 'PORT'}).text
                check_ip(ip, port)
            if len(ip_proxy_pool) > 20:
                print('代理池初始化完成', len(ip_proxy_pool))
                break
        except:
            print('请求{}页的ip代理出错，跳过'.format(i))


def check_ip(ip: str, port: str):
    proxy = {
        "http": 'http://' + ip + ':' + port,
        "https": 'http://' + ip + ':' + port
    }
    try:
        headers = {
            'User-Agent': ua_pool.get_ua()
        }
        response = requests.get(url='https://xa.ke.com/ershoufang/', headers=headers, proxies=proxy, timeout=3)
        if response.status_code == 200:
            print(proxy, '可用')
            if proxy not in ip_proxy_pool:
                ip_proxy_pool.append(proxy)
                write_file()
        else:
            print(proxy, '不可用')
    except:
        print(proxy, '请求异常')


def get_proxies():
    global ip_proxy_pool
    if len(ip_proxy_pool) != 0:
        return random.choice(ip_proxy_pool)

    with open('ip_proxy_pool.txt', encoding='utf-8') as ip_proxy:
        contents = ip_proxy.read()
        ip_proxy_pool = eval(contents)

    return random.choice(ip_proxy_pool)


def check_use_proxy():
    global ip_proxy_pool
    with open('ip_proxy_pool.txt', encoding='utf-8') as ip_proxy:
        contents = ip_proxy.read()
        if contents == '':
            print('文件为空，不需要校验')
            return
        ip_proxy_pool = eval(contents)
        if len(ip_proxy_pool) == 0:
            print('文件为空，不需要校验')
            return

    remove_list = []
    for proxy in ip_proxy_pool:
        try:
            headers = {
                'User-Agent': ua_pool.get_ua()
            }
            response = requests.get(url='https://xa.ke.com/ershoufang/', headers=headers, proxies=proxy, timeout=5)
            if response.status_code == 200:
                print(proxy, '可用')
            else:
                print(proxy, '不可用')
                remove_list.append(proxy)
        except:
            print(proxy, '请求异常')
            remove_list.append(proxy)

    for proxy in remove_list:
        if proxy in ip_proxy_pool:
            ip_proxy_pool.remove(proxy)

    write_file()


# 持久化
def write_file():
    file_path = 'ip_proxy_pool.txt'
    with open(file_path, mode='w', encoding='utf-8') as file_obj:
        file_obj.write(str(ip_proxy_pool))


if __name__ == '__main__':
    try:
        # init()
        # get_proxies()
        check_use_proxy()
    except Exception as e:
        print('出现异常，爬虫终止。。。', e)
        print(ip_proxy_pool)
    else:
        print('写入文件成功')
        print(ip_proxy_pool)
