import os
import random
import time
import urllib
from urllib.request import urlretrieve
import logging
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

PROXY_POOL_URL = 'http://liwudi.fun:56923/random'
logging.basicConfig(filename='my.log', level=logging.WARNING)


def get_split(lens=20, style='='):
    """
    get a series of splits,like "======"
    :param lens: the length of split string
    :param style: the char used to create split string
    :return: a string of split
    """
    s = ''
    for i in range(lens):
        s = s + style
    return s


def get_proxy():
    """
    get a proxy from liwudi.fun which create by me to collect
    ip proxies
    :return:
    """
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            return response.text
    except ConnectionError:
        return None


def random_proxy_header_access(url, proxy='', require_proxy=True, max_retry=10, sleep_time=1.2, random_proxy=True):
    """
    如果达到max_retry之后，仍然访问不到，返回空值
    use random header and proxy to access url and get content
    if access the url beyond max_retry, will return a blank string
    :param url:链接
    :param proxy:提供代理
    :param require_proxy:是否需要代理，默认为真
    :param max_retry:默认最大尝试10次
    :param sleep_time:每次爬取睡眠时间
    :return:返回爬取的网页或者最大尝试次数之后返回空
    :param random_proxy:随机使用代理，默认为真，随机使用真实地址而不使用代理
    """
    proxy_provide = False
    if len(proxy) == 0:
        proxy_provide = False
    else:
        proxy_provide = True
    for i in range(max_retry):
        html = ''
        try:
            if len(proxy) == 0 and require_proxy:
                proxy = get_proxy()
            elif (not proxy_provide) and require_proxy:
                proxy = get_proxy()
            logging.warning(proxy)
            ua = UserAgent()  # 实例化
            headers = {"User-Agent": ua.random}
            proxies = {'http': "http://" + proxy, 'https': 'http://' + proxy}
            logging.warning("第{}次准备爬取{}内容".format(str(i), url))
            if require_proxy and is_this_time_use_proxy:
                request = requests.get(url, headers=headers, proxies=proxies)
                logging.warning("随机使用代理")
            elif random_proxy and not is_this_time_use_proxy():
                request = requests.get(url, headers=headers)
                logging.warning("随机不使用代理")
            elif not random_proxy:
                request = requests.get(url, headers=headers)
            html = request.content
            logging.warning("爬取成功，返回内容")
            time.sleep(sleep_time)
        except Exception as result:
            logging.warning("错误信息:%s" % result)
            logging.warning("尝试重连")
            time.sleep(sleep_time)
        if len(html) != 0:
            logging.warning(get_split())
            return html
    return html


def is_this_time_use_proxy():
    """
    :return: return a bool value which decide whether use proxy this time
    """
    k = random.randint(0, 9)
    if k >= 5:
        return True
    else:
        return False


def retrieve_file(url, path, proxies="", require_proxy=True, max_retry=10, sleep_time=1.2, random_proxy=True):
    """
    retrieve file from provided url and save to path
    :param url: file url
    :param path: the save path
    :param proxies: proxy string, if this args not null, will always use this proxy if decide to use proxy
    :param require_proxy:decide whether use proxy
    :param max_retry: max times to retry if fail to retrieve
    :param sleep_time: thread sleep time which finish part function
    :param random_proxy: if this arg is true, whatever provide proxy, will random to use local address to access url
    :return:a bool value represent whether success to save file
    """
    success = False
    proxy_provide = False
    if len(proxies) == 0:
        proxy_provide = False
    else:
        proxy_provide = True
    for i in range(max_retry):
        logging.warning("第{}次准备抽取{}文件".format(str(i), url))
        try:
            if len(proxies) == 0 and require_proxy:
                proxies = get_proxy()
            if not proxy_provide and require_proxy:
                proxies = get_proxy()
            opener = urllib.request.build_opener()
            ua = UserAgent()
            if require_proxy and is_this_time_use_proxy():
                opener.addheaders = [('User-Agent', ua.random),
                                     ('proxy', "http://" + proxies),
                                     ('proxy', "https://" + proxies)]
            else:
                opener.addheaders = [('User-Agent', ua.random)]
            urllib.request.install_opener(opener)
            urlretrieve(url, path)
            logging.warning("文件提取成功")
            success = True
            time.sleep(sleep_time)
        except Exception as e:
            logging.warning("抽取失败:{}".format(e))
            time.sleep(sleep_time)
        if success:
            return success
            time.sleep(sleep_time)
    if not success:
        logging.warning("{}提取失败".format(url))
        time.sleep(sleep_time)
        return success


def get_pdf_url_by_doi(doi, work_path, sleep_time=1.2, max_retry=10):
    """
    save file from sci_hub by doi string provided
    :param doi: paper doi
    :param work_path: file path to save
    :param sleep_time: thread sleep time which finish part function
    :param max_retry: max times to retry if fail to retrieve
    :return:
    """
    domain_list = ['sci-hub.se/', 'sci-hub.st/', 'sci-hub.ru/']
    html = ''
    for i in range(max_retry):
        url = 'https://' + domain_list[random.randint(0, 2)] + doi
        html = random_proxy_header_access(url, get_proxy(), max_retry=1)
        if len(html) != 0:
            break
    if len(html) == 0:
        logging.warning("获取html文件达到最大次数，停止获取doi:{}".format(doi))
        print("获取html文件达到最大次数，停止获取doi:{}".format(doi))
        return
    attr_list = get_attribute_of_html(html, {"href=": "in"}, ["button"])
    for paths in attr_list:
        paths = str(paths)
        try:
            path = paths.split("href=")[1].split("?download")[0]
        except Exception as e:
            logging.warning("链接抽取错误:{}".format(e))
            continue
        time.sleep(sleep_time)
        for i in range(max_retry):
            success = retrieve_file(
                'https://' + domain_list[random.randint(0, 2)] + path.replace('\'', '').replace('\\', ''),
                work_path, get_proxy(), require_proxy=True, max_retry=1)
            if success:
                break
        if not success:
            logging.warning("抽取文件达到最大次数，停止获取doi:{}".format(doi))
            print("抽取文件达到最大次数，停止获取doi:{}".format(doi))


def verify_rule(rule, element):
    """
    verify the element string. if element satisfy all rules provided by rule arg,
    return true.
    :param rule:a dictionary that represent rules. the key is the match string and the value
    is the rule. The rule is only support "in" and "not in". example:{"href": "in"}
    :param element:the string will be verified
    :return:a bool value represent whether element satisfy all rule
    """
    for key, value in rule.items():
        if str(value) == 'in' and str(key) not in str(element):
            return False
        elif str(value) == 'not in' and str(key) in str(element):
            return False
    return True


def get_attribute_of_html(html, rule=None, attr_list=None):
    """
    Use beautifulsoup4 to scan the html string get by urllib.get().
    And select all attribute in attr_list and then select satisfy all rules in rule
    in list.then return the list which contains all attribute
    :param html: html string
    :param rule: a dictionary that represent rules. the key is the match string and the value
    is the rule. The rule is only support "in" and "not in". example:{"href": "in"}
    :param attr_list: a list that contain attribute which you want. example:["a", "button"]
    :return: a list of attribute string
    """
    if attr_list is None:
        attr_list = ['a']
    if rule is None:
        rule = {'href': 'in'}
    list = []
    if len(html) == 0:
        return list
    bs = BeautifulSoup(html, 'html.parser')
    elements_list = []
    for k in attr_list:
        elements_list.extend(bs.find_all(k))
    for elements in elements_list:
        if verify_rule(rule, elements):
            list.append(str(elements))
    return list


def local_path_generate(folder_name, file_name=""):
    """
    create a folder whose name is folder_name in folder which code in if folder_name
    is not exist. and then concat pdf_name to create file path.
    :param folder_name: 待创建的文件夹名称
    :param file_name: 文件名称，带后缀格式
    :return: 返回文件绝对路径
    """
    if os.path.exists(folder_name):
        logging.warning("文件夹存在")
    else:
        os.makedirs(folder_name)
    if len(file_name):
        file_name = str(time.strftime("%H_%M_%S", time.localtime()))
        file_name = file_name + ".pdf"
    dir = os.path.abspath(folder_name)
    work_path = os.path.join(dir, '').format(file_name)
    return work_path


if __name__ == "__main__":
    dir = os.path.abspath("PAMI_sum")
    work_path = os.path.join(dir, '3.pdf')
    get_pdf_url_by_doi("10.1109/TPAMI.2020.3042298", work_path)
