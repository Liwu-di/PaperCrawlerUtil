import os
import random
import time
import urllib
from urllib.request import urlretrieve
import logging
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pandas
import pdfplumber
import http.client
import hashlib
import json

PROXY_POOL_URL = "http://liwudi.fun:56923/random"
logging.basicConfig(filename='../my.log', level=logging.WARNING)
log_style = "log"

EQUAL = "equal"
NOT_EQUAL = "not equal"
IN = "in"
NOT_IN = "not in"

LOG_STYLE_LOG = "log"
LOG_STYLE_PRINT = "print"
LOG_STYLE_ALL = "all"

def log(string):
    global log_style
    if log_style == "log":
        logging.warning(string)
    elif log_style == "print":
        print(string)
    elif log_style == "all":
        logging.warning(string)
        print(string)


def basic_config(log_file_name="../my.log", log_level=logging.WARNING,
                 proxy_pool_url="http://liwudi.fun:56923/random",
                 logs_style="log"):
    """

    :param log_file_name: 日志文件名称
    :param log_level: 日志等级
    :param proxy_pool_url: 代理获取地址
    :param logs_style: log表示使用日志文件，print表示使用控制台，all表示两者都使用
    :return:
    """
    global PROXY_POOL_URL
    global log_style
    PROXY_POOL_URL = proxy_pool_url
    log_style = logs_style


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
            log(proxy)
            ua = UserAgent()  # 实例化
            headers = {"User-Agent": ua.random}
            proxies = {'http': "http://" + proxy, 'https': 'http://' + proxy}
            log("第{}次准备爬取{}内容".format(str(i), url))
            if require_proxy:
                if random_proxy and is_this_time_use_proxy():
                    log("随机使用代理")
                    request = requests.get(url, headers=headers, proxies=proxies)
                elif random_proxy and not is_this_time_use_proxy():
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
            if require_proxy and is_this_time_use_proxy():
                opener.addheaders = [('User-Agent', ua.random),
                                     ('proxy', "http://" + proxies),
                                     ('proxy', "https://" + proxies)]
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
        log("获取html文件达到最大次数，停止获取doi:{}".format(doi))
        return
    attr_list = get_attribute_of_html(html, {"href=": "in"}, ["button"])
    for paths in attr_list:
        paths = str(paths)
        try:
            path = paths.split("href=")[1].split("?download")[0]
        except Exception as e:
            log("链接抽取错误:{}".format(e))
            continue
        time.sleep(sleep_time)
        for i in range(max_retry):
            success = retrieve_file(
                'https://' + domain_list[random.randint(0, 2)] + path.replace('\'', '').replace('\\', ''),
                work_path, get_proxy(), require_proxy=True, max_retry=1)
            if success:
                break
        if not success:
            log("抽取文件达到最大次数，停止获取doi:{}".format(doi))


def verify_rule(rule, element):
    """
    verify the element string. if element satisfy all rules provided by rule arg,
    return true.
    :param rule:a dictionary that represent rules. the key is the match string and the value
    is the rule. The rule is only support "in" and "not in" and "equal" and "not equal".
     example:{"href": "in"}
    :param element:the string will be verified
    :return:a bool value represent whether element satisfy all rule
    """
    for key, value in rule.items():
        if str(value) == IN and str(key) not in str(element):
            return False
        elif str(value) == NOT_IN and str(key) in str(element):
            return False
        elif str(value) == EQUAL and str(value) != str(element):
            return False
        elif str(value) == NOT_EQUAL and str(value) == str(element):
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
        log("文件夹存在")
    else:
        os.makedirs(folder_name)
    if len(file_name) == 0:
        file_name = str(time.strftime("%H_%M_%S", time.localtime()))
        file_name = file_name + ".pdf"
    dir = os.path.abspath(folder_name)
    work_path = os.path.join(dir, file_name)
    return work_path


def write_file(path, mode, string, encoding="utf-8"):
    try:
        with open(path, mode=mode, encoding=encoding) as f:
            f.write(string)
        f.close()
        log("写入文件{}成功".format(path))
    except Exception as e:
        log("写入文件{}失败：{}".format(path, e))


def get_para_from_one_pdf(path, begin_tag=None, end_tag=None, ranges=(0, 1)):
    """
        用来从pdf文件中获取一些文字，可以通过设置开始或者结束标志，以及页码范围获取自己想要的内容
        如果是文件夹，则直接遍历文件夹中所有的PDF，返回所有符合的字符串，同时可以设置分隔符
        :param path: pdf path
        :param begin_tag: the tag which will begin from this position to abstract text
        :param end_tag: the tag which will end util this position to abstract text
        :param ranges: which pages you want to abstract
        :return: the string
    """
    txt = ""
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) >= 0:
            for i in range(ranges[0], ranges[1] + 1):
                txt = txt + pdf.pages[i].extract_text()
            if len(begin_tag) == 0 and len(end_tag) == 0:
                txt = txt
            elif len(begin_tag) == 0 and len(end_tag) > 0:
                ele = ""
                for ele in end_tag:
                    if txt.find(ele):
                        break
                txt = txt.split(ele)[0]
            elif len(begin_tag) > 0 and len(end_tag) == 0:
                ele = ""
                for ele in begin_tag:
                    if txt.find(ele):
                        break
                txt = txt.split(ele)[1]
            elif len(begin_tag) > 0 and len(end_tag) > 0:
                ele1 = ""
                ele2 = ""
                for ele1 in begin_tag:
                    if txt.find(ele1):
                        break
                for ele2 in end_tag:
                    if txt.find(ele2):
                        break
                txt = txt.split(ele1)[1].split(ele2)[0]
    pdf.close()
    return txt


def get_para_from_pdf(path, begin_tag=None, end_tag=None, ranges=(0, 1), split_style="==="):
    """
    用来从pdf文件中获取一些文字，可以通过设置开始或者结束标志，以及页码范围获取自己想要的内容
    如果是文件夹，则直接遍历文件夹中所有的PDF，返回所有符合的字符串，同时可以设置分隔符
    :param path: pdf path
    :param begin_tag: the tag which will begin from this position to abstract text
    :param end_tag: the tag which will end util this position to abstract text
    :param ranges: which pages you want to abstract
    :param split_style: split style which will used to split string of each file of directory
    :return: the string
    """
    if begin_tag is None:
        begin_tag = []
    if end_tag is None:
        end_tag = ["1. Introduction", "1. introduction", "Introduction", "introduction"]
    txt = ""
    valid_count = 0
    sum_count = 0
    file_list = []
    if os.path.isfile(path):
        file_list.append(path)
    else:
        file_list.extend(getAllFiles(path))
    for ele in file_list:
        if ele.endswith("pdf"):
            tem = get_para_from_one_pdf(ele, begin_tag, end_tag, ranges)
            txt = txt + tem + "\n"
            txt = txt + get_split(style=split_style) + get_split(style="\n", lens=3)
            if len(tem) > 0:
                valid_count = valid_count + 1
                log("有效抽取文件：{}".format(ele))
            sum_count = sum_count + 1
        else:
            sum_count = sum_count + 1
            log("错误：{}不是PDF文件".format(ele))
    log("总计抽取了文件数量：{}，其中有效抽取（>0）数量：{}".format(sum_count, valid_count))
    return txt


def getAllFiles(targetDir):
    """
    遍历文件夹
    :param targetDir: 遍历的文件夹
    :return: 所有文件的名称
    """
    files = []
    listFiles = os.listdir(targetDir)
    for i in range(0, len(listFiles)):
        path = os.path.join(targetDir, listFiles[i])
        if os.path.isdir(path):
            files.extend(getAllFiles(path))
        elif os.path.isfile(path):
            files.append(path)
    return files


def sentence_translate(string, appid="20200316000399558", secret_key="BK6HRAv6QJDGBwaZgr4F"):
    httpClient = None
    myurl = '/api/trans/vip/translate'
    fromLang = 'auto'  # 原文语种
    toLang = 'zh'  # 译文语种
    salt = random.randint(32768, 65536)
    q = string
    sign = appid + q + str(salt) + secret_key
    sign = hashlib.md5(sign.encode()).hexdigest()
    myurl = myurl + '?appid=' + appid + '&q=' + urllib.parse.quote(
        q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(
        salt) + '&sign=' + sign
    result = {}
    try:
        httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
        httpClient.request('GET', myurl)
        response = httpClient.getresponse()
        result_all = response.read().decode("utf-8")
        result = json.loads(result_all)
        time.sleep(1.2)
    except Exception as e:
        log(e)
        time.sleep(1.2)
    finally:
        if httpClient:
            httpClient.close()
    res = ""
    try:
        res = res + result["trans_result"][0]["dst"]
    except Exception as e:
        log("翻译错误：{}".format(e))
    return res


def text_translate(path, appid="20200316000399558", secret_key="BK6HRAv6QJDGBwaZgr4F"):
    line = ""
    res = ""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for ele in lines:
            line = line + ele
            if len(line) >= 3000:
                line = line.replace("\n", "")
                res = res + sentence_translate(line)
                line = ""
    f.close()
    if len(line) > 0:
        res = res + sentence_translate(line)
    return res


if __name__ == "__main__":
    basic_config(logs_style=LOG_STYLE_PRINT)
    write_file(path=local_path_generate("E:\\git-code\\paper-crawler\\CVPR\\CVPR_2021\\3\\3", "2.txt"),
               mode="w+",
               string=text_translate("E:\\git-code\\paper-crawler\\CVPR\\CVPR_2021\\3\\3\\title_and_abstract.txt"))
