import time
import urllib
from urllib.request import urlretrieve
from requests.cookies import RequestsCookieJar
import requests
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent

from common_util import *


def random_proxy_header_access(url: str, proxy: str = '',
                               require_proxy: bool = False, max_retry: int = 10, sleep_time: float = 1.2,
                               random_proxy: bool = True, time_out: tuple = (10, 20),
                               need_log: bool = True, cookie: str = "", if_bytes_encoding: str = "utf-8",
                               method: str = GET, get_params: List[tuple] or dict or bytes = None,
                               post_data: dict or List[tuple] or bytes = None,
                               json=None, allow_redirects: bool = True) -> str:
    """
    如果达到max_retry之后，仍然访问不到，返回空值
    use random header and proxy to access url and get content
    if access the url beyond max_retry, will return a blank string
    :param allow_redirects: 是否启用重定向
    :param json: 请求体json序列化对象
    :param method: 请求方法
    :param post_data: POST方式的请求体数据
    :param get_params: URL参数
    :param if_bytes_encoding: 如果爬取到的是字节，需要通过什么字符集转换
    :param cookie: 对于需要cookie即登录才能访问的网站，需要提供cookie
    :param need_log: 是否需要日志
    :param url:链接
    :param proxy:提供代理
    :param require_proxy:是否需要代理，默认为真
    :param max_retry:默认最大尝试10次
    :param sleep_time:每次爬取睡眠时间
    :return:返回爬取的网页或者最大尝试次数之后返回空
    :param random_proxy:随机使用代理，默认为真，随机使用真实地址而不使用代理
    :param time_out: 一个元组或者浮点数，元组前者表示连接超时阈值，后者表示获取内容超时阈值、
                    如果是浮点数，则两者值设为一样
    """
    proxy_provide = False
    cookie_jar = RequestsCookieJar()
    if len(cookie) != 0:
        cookie_jar = cookieString2CookieJar(cookie)
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
                if need_log:
                    log("使用代理：{}".format(proxy))
            ua = UserAgent()  # 实例化
            headers = {"User-Agent": ua.random}
            proxies = {'http': "http://" + proxy, 'https': 'http://' + proxy}
            if need_log:
                log("第{}次准备爬取{}的内容".format(str(i), url))
            if require_proxy:
                if random_proxy and two_one_choose():
                    if need_log:
                        log("随机使用代理")
                    request = requests.request(method=method, url=url, headers=headers, proxies=proxies,
                                               timeout=time_out, cookies=cookie_jar, allow_redirects=allow_redirects,
                                               json=json, data=post_data, params=get_params)
                elif random_proxy and not two_one_choose():
                    if need_log:
                        log("随机不使用代理")
                    request = requests.request(method=method, url=url, headers=headers, timeout=time_out,
                                               cookies=cookie_jar, allow_redirects=allow_redirects,
                                               json=json, data=post_data, params=get_params)
                elif not random_proxy:
                    request = requests.request(method=method, url=url, headers=headers, proxies=proxies,
                                               timeout=time_out, cookies=cookie_jar, allow_redirects=allow_redirects,
                                               json=json, data=post_data, params=get_params)
                else:
                    request = requests.request(method=method, url=url, headers=headers, proxies=proxies,
                                               timeout=time_out, cookies=cookie_jar, allow_redirects=allow_redirects,
                                               json=json, data=post_data, params=get_params)
            else:
                request = requests.request(method=method, url=url, headers=headers, timeout=time_out, cookies=cookie_jar
                                           , allow_redirects=allow_redirects, json=json, data=post_data,
                                           params=get_params)
            html = request.content
            if need_log:
                log("爬取成功，返回内容")
            time.sleep(sleep_time)
        except NoProxyException as e:
            raise e
        except Exception as result:
            log("错误信息:%s" % result)
            log("尝试重连")
            time.sleep(sleep_time)
        if len(html) != 0:
            log(get_split(lens=100))
            if type(html) == bytes:
                try:
                    html = str(html, encoding=if_bytes_encoding)
                except Exception as e:
                    log("字节转字符串错误：{}".format(e))
            return html
    return html


def retrieve_file(url: str, path: str, proxies: str = "",
                  require_proxy: bool = False, max_retry: int = 10,
                  sleep_time: float = 1.2, random_proxy: bool = True,
                  need_log: bool = True, reporthook: Callable[[], None] = None,
                  data: str = None) -> bool:
    """
    retrieve file from provided url and save to path
    :param data: 使用url encode的参数
    :param reporthook: 用来在获取url链接信息之后调用的函数,例如函数def test(a: int, b: int, c: int) -> None,
    三个参数分别表示，当前下载第几块，每块的大小，文件的总大小
    :param need_log: 是否需要日志
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
        if need_log:
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
            bar = None
            if reporthook:
                reporthook = reporthook
            else:
                bar = process_bar(final_prompt="文件下载完成")
                reporthook = bar.process
            urlretrieve(url=url, filename=path, reporthook=reporthook, data=data)
            # if need_log:
            #     log("文件提取成功")
            success = True
            time.sleep(sleep_time)
        except NoProxyException as e:
            raise e
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


def get_pdf_url_by_doi(doi: str, work_path: str, sleep_time: float = 1.2, max_retry: int = 10,
                       require_proxy: bool = False, random_proxy: bool = True,
                       proxies: bool = "", need_log: bool = True) -> None:
    """
    save file from sci_hub by doi string provided
    :param need_log: 是否需要日志
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
            if need_log:
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
                if need_log:
                    log("文件{}提取成功".format(work_path))
                break
        if not success:
            log("抽取文件达到最大次数，停止获取doi:{}".format(doi))


def verify_rule(rule: dict, origin: float or str or Tag) -> bool:
    """
    verify the element string. if element satisfy all rules provided by rule arg,
    return true.
    :param rule:a dictionary that represent rules. the key is the match string and the value
    is the rule. The rule is only support "in" and "not in" and "equal" and "not equal",
    and more than, less than and greater or equal and less than or equal.
     example:{"href": "in"}
    :param origin:the string will be verified
    :return:a bool value represent whether element satisfy all rule
    """
    if rule is None or len(rule) == 0:
        return True
    if origin is None:
        return False
    for key, value in rule.items():
        if str(value) == IN and str(key) not in str(origin):
            return False
        elif str(value) == NOT_IN and str(key) in str(origin):
            return False
        elif str(value) == EQUAL and str(key) != str(origin):
            return False
        elif str(value) == NOT_EQUAL and str(key) == str(origin):
            return False
        elif str(value) == LESS_THAN or str(value) == LESS_THAN or str(value) == LESS_THAN_AND_EQUAL or str(
                value) == MORE_THAN or str(value) == GREATER_AND_EQUAL:
            if type(origin) != float:
                return False
            else:
                if str(value) == LESS_THAN and float(origin) >= float(key):
                    return False
                elif str(value) == LESS_THAN_AND_EQUAL and float(origin) > float(key):
                    return False
                elif str(value) == GREATER_AND_EQUAL and float(origin) < float(key):
                    return False
                elif str(value) == MORE_THAN and float(origin) <= float(key):
                    return False
    return True


def get_attribute_of_html(html: str, rule: dict = None, attr_list: list = None) -> list:
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


def get_pdf_form_arXiv(title: str, folder_name: str, sleep_time: float = 1.2,
                       max_retry: int = 10, require_proxy: bool = False,
                       random_proxy: bool = True, proxies: str = "", max_get: int = 3) -> None:
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
