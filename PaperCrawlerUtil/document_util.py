import hashlib
import http
import json
import urllib

import pdfplumber
from googletrans import Translator
from pdf2docx import Converter

from common_util import *


def baidu_translate(string,
                    appid,
                    secret_key,
                    src="auto",
                    dst="zh",
                    sleep_time=1.2):
    """
    百度翻译
    :param string:
    :param appid:
    :param secret_key:
    :param src:
    :param dst:
    :param sleep_time:
    :return:
    """
    log("时间：{}使用百度翻译".format(str(time.strftime("%H_%M_%S", time.localtime()))))
    httpClient = None
    myurl = '/api/trans/vip/translate'
    fromLang = src  # 原文语种
    toLang = dst  # 译文语种
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
        time.sleep(sleep_time)
    except Exception as e:
        log(e)
        time.sleep(sleep_time)
    finally:
        if httpClient:
            httpClient.close()
    res = ""
    try:
        res = result["trans_result"][0]["dst"]
    except Exception as e:
        log("翻译错误：{}".format(e))
    return res


def google_translate(string, src='en', dest='zh-cn', proxies=None, sleep_time=1.2):
    """
    谷歌翻译
    @todo 提供一个源语言和目的语言的表
    :param string:
    :param src:
    :param dest:
    :param proxies:
    :param sleep_time:
    :return:
    """
    urls = ['translate.google.cn', 'translate.google.com']
    if proxies is None:
        proxies = {'http': 'http://127.0.0.1:1080'}
    log("时间：{}使用谷歌翻译".format(str(time.strftime("%H_%M_%S", time.localtime()))))
    try:
        translator = Translator(service_urls=urls, proxies=proxies)
        trans = translator.translate(string, src=src, dest=dest)
        time.sleep(sleep_time)
        return trans.text
    except Exception as e:
        log("翻译错误：{}".format(e))
        time.sleep(sleep_time)
    return ""


def sentence_translate(string, appid, secret_key, max_retry, proxies, probability, is_google):
    """
    随机使用百度谷歌翻译句子
    :param string: 待翻译语句
    :param appid: 百度翻译appid
    :param secret_key: 百度翻译密钥
    :param max_retry: 最大尝试次数
    :param proxies: 代理
    :param probability: 两种翻译的使用概率
    :param is_google: 是否使用谷歌翻译
    :return:
    """
    for i in range(max_retry):
        res = ""
        if is_google:
            if two_one_choose(probability):
                res = baidu_translate(string, appid, secret_key)
            else:
                res = google_translate(string, proxies=proxies)
            if len(res) == 0:
                continue
            else:
                return res
        else:
            res = baidu_translate(string, appid, secret_key)
            if len(res) == 0:
                continue
            else:
                return res
    return ""


def text_translate(path,
                   appid,
                   secret_key,
                   max_retry=10,
                   is_google=True,
                   probability=0.5,
                   proxies=None):
    """
    文本翻译，根据提供的文件地址，翻译文件内容
    :param path: 文本路径
    :param appid: 百度翻译appid
    :param secret_key: 百度翻译密钥
    :param max_retry: 最大尝试次数
    :param is_google: 是否使用谷歌翻译
    :param proxies: 代理，样例{'http': 'http://127.0.0.1:1080'}
    :param probability:百度和谷歌翻译之间使用的比例，大于该值使用百度翻译，否则谷歌翻译
    :return:
    """
    line = ""
    res = ""
    if is_google and proxies is None:
        log("使用谷歌翻译，但是没有提供代理，尝试使用代理：{'http': 'http://127.0.0.1:1080'}")
        proxies = {'http': 'http://127.0.0.1:1080'}
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for ele in lines:
            line = line + ele
            if len(line) >= 3000:
                line = line.replace("\n", " ")
                res = res + sentence_translate(line, appid, secret_key, max_retry, proxies, probability, is_google)
                line = ""
    f.close()
    if len(line) > 0:
        res = res + sentence_translate(line, appid, secret_key, max_retry, proxies, probability, is_google)
    return res


def pdf2docx(pdf_path, word_path, end_pages=None, start_pages=None):
    """
    转换pdf 到word文件，可以自动识别是文件夹还是单个文件，其中word_path表示的生成的word的文件夹，不论是
    单个还是文件夹批量转换，这个值都是文件夹
    :param pdf_path: pdf的路径
    :param word_path: 用于存放word的路径
    :param end_pages: 结束页码
    :param start_pages: 开始页码
    :return:
    """
    file_list = []
    file = True
    count = 0
    if os.path.isfile(pdf_path) and os.path.isfile:
        file_list.append(pdf_path)
        log("转换文件{}开始".format(pdf_path))
    else:
        file_list.extend(getAllFiles(pdf_path))
        log("获取文件夹{}文件成功".format(pdf_path))
        file = False
    for ele in file_list:
        if ele.endswith(".pdf"):
            try:
                cv = Converter(ele)
                if not file:
                    cv.convert(local_path_generate(word_path), start=start_pages, end=end_pages)
                else:
                    cv.convert(word_path, start=start_pages, end=end_pages)
                    count = count + 1
                log("总计pdf文件个数{}，已经完成{}".format(len(file_list), count))
            except Exception as e:
                log("转换失败文件{},{}".format(ele, e))
            finally:
                cv.close()


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
    try:
        with pdfplumber.open(path) as pdf:
            if len(pdf.pages) >= 0:
                left_range = ranges[0]
                right_range = ranges[1] + 1
                if right_range >= len(pdf.pages):
                    right_range = len(pdf.pages)
                if left_range >= len(pdf.pages):
                    left_range = 0
                for i in range(left_range, right_range):
                    txt = txt + pdf.pages[i].extract_text()
                if len(begin_tag) == 0 and len(end_tag) == 0:
                    txt = txt
                elif len(begin_tag) == 0 and len(end_tag) > 0:
                    ele = ""
                    for e in end_tag:
                        if txt.find(e) >= 0:
                            ele = e
                            break
                    if len(ele) > 0:
                        txt = txt.split(ele)[0]
                elif len(begin_tag) > 0 and len(end_tag) == 0:
                    ele = ""
                    for e in begin_tag:
                        if txt.find(e) >= 0:
                            ele = e
                            break
                    if len(ele) > 0:
                        txt = txt.split(ele)[1]
                elif len(begin_tag) > 0 and len(end_tag) > 0:
                    ele1 = ""
                    ele2 = ""
                    for e1 in begin_tag:
                        if txt.find(e1) >= 0:
                            ele1 = e1
                            break
                    for e2 in end_tag:
                        if txt.find(e2) >= 0:
                            ele2 = e2
                            break
                    if len(ele1) > 0 and len(ele2) > 0:
                        txt = txt.split(ele1)[1].split(ele2)[0]
        pdf.close()
        return txt
    except Exception as e:
        log("打开PDF异常：{}".format(e))
        return txt


def get_para_from_pdf(path, begin_tag=None, end_tag=None, ranges=(0, 1), split_style="===", valid_threshold=0):
    """
    用来从pdf文件中获取一些文字，可以通过设置开始或者结束标志，以及页码范围获取自己想要的内容
    如果是文件夹，则直接遍历文件夹中所有的PDF，返回所有符合的字符串，同时可以设置分隔符
    :param valid_threshold: decide whether paragraph digest success
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
        end_tag = ["1. Introduction", "1. introduction",
                   "Introduction", "introduction",
                   "1.摘要", "1. 摘要", "1.", "1"]
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
            if len(tem) > valid_threshold:
                valid_count = valid_count + 1
                log("有效抽取文件：{}".format(ele))
            else:
                log("抽取文件疑似失败：{}".format(ele))
            sum_count = sum_count + 1
        else:
            sum_count = sum_count + 1
            log("错误：{}不是PDF文件".format(ele))
    log("总计抽取了文件数量：{}，其中有效抽取（>{}）数量：{}".format(sum_count, valid_threshold, valid_count))
    return txt


def getAllFiles(target_dir):
    """
    遍历文件夹
    :param target_dir: 遍历的文件夹
    :return: 所有文件的名称
    """
    files = []
    listFiles = os.listdir(target_dir)
    for i in range(0, len(listFiles)):
        path = os.path.join(target_dir, listFiles[i])
        if os.path.isdir(path):
            files.extend(getAllFiles(path))
        elif os.path.isfile(path):
            files.append(path)
    return files


if __name__ == "__main__":
    basic_config(logs_style=LOG_STYLE_PRINT)
