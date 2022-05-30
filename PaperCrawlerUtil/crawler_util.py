import time
import urllib
from urllib.request import urlretrieve

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from common_util import *


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
            if require_proxy:
                log("使用代理：{}".format(proxy))
            ua = UserAgent()  # 实例化
            headers = {"User-Agent": ua.random}
            proxies = {'http': "http://" + proxy, 'https': 'http://' + proxy}
            log("第{}次准备爬取{}的内容".format(str(i), url))
            if require_proxy:
                if random_proxy and two_one_choose():
                    log("随机使用代理")
                    request = requests.get(url, headers=headers, proxies=proxies)
                elif random_proxy and not two_one_choose():
                    log("随机不使用代理")
                    request = requests.get(url, headers=headers)
                elif not random_proxy:
                    request = requests.get(url, headers=headers, proxies=proxies)
                else:
                    request = requests.get(url, headers=headers, proxies=proxies)
            else:
                request = requests.get(url, headers=headers)
            html = request.content
            log("爬取成功，返回内容")
            time.sleep(sleep_time)
        except Exception as result:
            log("错误信息:%s" % result)
            log("尝试重连")
            time.sleep(sleep_time)
        if len(html) != 0:
            log(get_split())
            return html
    return html


def retrieve_file(url, path, proxies="", require_proxy=True, max_retry=10, sleep_time=1.2, random_proxy=True):
    """
    retrieve file from provided url and save to path
    :param url: file url
    :param path: the save path
    :param proxies: proxy string, if this args not null, will always use this proxy if decide to use proxy
    :param require_proxy:decide whether use proxy
    :param max_retry: max times to retry if fail to retrieve
    :param sleep_time: thread sleep time which finish part function
    :param random_proxy: if this arg is true, whatever provide proxy,
    will random to use local address to access url
    :return:a bool value represent whether success to save file
    """
    success = False
    proxy_provide = False
    if len(proxies) == 0:
        proxy_provide = False
    else:
        proxy_provide = True
    for i in range(max_retry):
        log("第{}次准备抽取{}文件".format(str(i), url))
        try:
            if len(proxies) == 0 and require_proxy:
                proxies = get_proxy()
            if not proxy_provide and require_proxy:
                proxies = get_proxy()
            opener = urllib.request.build_opener()
            ua = UserAgent()
            if require_proxy:
                if random_proxy and two_one_choose():
                    opener.addheaders = [('User-Agent', ua.random),
                                         ('proxy', "http://" + proxies),
                                         ('proxy', "https://" + proxies)]
                elif random_proxy and not two_one_choose():
                    opener.addheaders = [('User-Agent', ua.random)]
                else:
                    opener.addheaders = [('User-Agent', ua.random)]
            else:
                opener.addheaders = [('User-Agent', ua.random)]
            urllib.request.install_opener(opener)
            urlretrieve(url, path)
            log("文件提取成功")
            success = True
            time.sleep(sleep_time)
        except Exception as e:
            log("抽取失败:{}".format(e))
            time.sleep(sleep_time)
        if success:
            return success
            time.sleep(sleep_time)
    if not success:
        log("{}提取失败".format(url))
        time.sleep(sleep_time)
        return success


def get_pdf_url_by_doi(doi, work_path, sleep_time=1.2, max_retry=10,
                       require_proxy=False, random_proxy=True, proxies=""):
    """
    save file from sci_hub by doi string provided
    :param require_proxy:
    :param random_proxy:
    :param proxies:
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
        html = random_proxy_header_access(url,
                                          max_retry=1, proxy=proxies,
                                          random_proxy=random_proxy,
                                          require_proxy=require_proxy)
        if len(html) == 0:
            log("爬取失败，字符串长度为0")
            time.sleep(sleep_time)
            continue
        elif len(html) != 0 and len(get_attribute_of_html(html, {"href=": "in"}, ["button"])) == 0:
            log("爬取失败，无法从字符串中提取需要的元素")
            time.sleep(sleep_time)
            continue
        else:
            log("从sichub获取目标文件链接成功，等待分析提取")
            break
    if len(html) == 0:
        log("获取html文件达到最大次数，停止获取doi:{}".format(doi))
        return
    attr_list = get_attribute_of_html(html, {"href=": "in"}, ["button"])
    for paths in attr_list:
        paths = str(paths)
        try:
            path = paths.split("href=")[1].split("?download")[0]
        except Exception as e:
            log("链接{}截取错误:{}".format(paths, e))
            continue
        time.sleep(sleep_time)
        for i in range(max_retry):
            path = path.replace("'", "").replace("\"", "").replace(",", "")
            if (not path.startswith("http:")) and (not path.startswith("https:")):
                path = "https://" + (path.replace("//", "", 1))
            else:
                path = path
            success = retrieve_file(
                path,
                work_path, proxies=proxies, require_proxy=require_proxy, max_retry=1)
            if success:
                log("文件{}提取成功".format(work_path))
                break
        if not success:
            log("抽取文件达到最大次数，停止获取doi:{}".format(doi))


def verify_rule(rule, origin):
    """
    verify the element string. if element satisfy all rules provided by rule arg,
    return true.
    :param rule:a dictionary that represent rules. the key is the match string and the value
    is the rule. The rule is only support "in" and "not in" and "equal" and "not equal".
     example:{"href": "in"}
    :param origin:the string will be verified
    :return:a bool value represent whether element satisfy all rule
    """
    if rule is None or len(rule) == 0:
        return True
    if origin is None or len(origin) == 0:
        return False
    for key, value in rule.items():
        if str(value) == IN and str(key) not in str(origin):
            return False
        elif str(value) == NOT_IN and str(key) in str(origin):
            return False
        elif str(value) == EQUAL and str(value) != str(origin):
            return False
        elif str(value) == NOT_EQUAL and str(value) == str(origin):
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


def get_pdf_form_arXiv(title, folder_name, sleep_time=1.2, max_retry=10,
                       require_proxy=True, random_proxy=True, proxies="",
                       max_get=3):
    """
    从arXiv获取论文，
    :param title:
    :param folder_name:
    :param sleep_time:
    :param max_retry:
    :param require_proxy:
    :param random_proxy:
    :param proxies:
    :param max_get: 当搜索结果有多个时，最多获取的数量
    :return:
    """
    html = random_proxy_header_access(url="https://arxiv.org/search/?query="
                                          + title.replace(" ", "+")
                                          + "&searchtype=all&source=header",
                                      proxy=proxies, require_proxy=require_proxy, max_retry=max_retry,
                                      sleep_time=sleep_time, random_proxy=random_proxy)
    attr_list = get_attribute_of_html(html, rule={"pdf": IN, "arxiv": IN, "href": IN})
    count = 0
    for k in attr_list:
        path = k.split("href=\"")[1].split("\"")[0]
        retrieve_file(path,
                      local_path_generate(folder_name=folder_name, file_name=title + str(count) + ".pdf"),
                      proxies=proxies, require_proxy=require_proxy,
                      max_retry=max_retry, sleep_time=sleep_time, random_proxy=random_proxy)
        count = count + 1
        if count >= max_get:
            break
    get_split()


if __name__ == "__main__":
    basic_config(logs_style=LOG_STYLE_PRINT)
