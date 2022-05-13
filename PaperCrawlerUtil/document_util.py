import hashlib
import http
import json
import time
import urllib
import pdfplumber
from googletrans import Translator
from pdf2docx import Converter
from common_util import *


def baidu_translate(string,
                    appid="20200316000399558",
                    secret_key="BK6HRAv6QJDGBwaZgr4F",
                    src="auto",
                    dst="zh",
                    sleep_time=1.2):
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


def google_translate(string, src='en', dest='zh-cn', is_proxy=True, proxies=None, sleep_time=1.2):
    urls = ['translate.google.cn']
    if is_proxy and proxies is None:
        proxies = {'http': 'http://127.0.0.1:1080'}
    log("时间：{}使用谷歌翻译".format(str(time.strftime("%H_%M_%S", time.localtime()))))
    if is_proxy:
        urls.append('translate.google.com')
    try:
        translator = Translator(service_urls=urls, proxies=proxies)
        trans = translator.translate(string, src=src, dest=dest)
        time.sleep(sleep_time)
        return trans.text
    except Exception as e:
        log("翻译错误：{}".format(e))
        time.sleep(sleep_time)
    return ""


def sentence_translate(string, appid, secret_key, is_proxy, max_retry):
    for i in range(max_retry):
        res = ""
        if two_one_choose():
            res = baidu_translate(string, appid, secret_key)
        else:
            res = google_translate(string, is_proxy=is_proxy)
        if len(res) == 0:
            continue
        else:
            return res
    return ""


def text_translate(path, appid="20200316000399558", secret_key="BK6HRAv6QJDGBwaZgr4F", max_retry=10, is_proxy=True):
    line = ""
    res = ""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for ele in lines:
            line = line + ele
            if len(line) >= 3000:
                line = line.replace("\n", " ")
                res = res + sentence_translate(line, appid, secret_key, is_proxy, max_retry)
                line = ""
    f.close()
    if len(line) > 0:
        res = res + sentence_translate(line, appid, secret_key, is_proxy, max_retry)
    return res


def pdf2docx(pdf_path, word_path, end_pages=None, start_pages=None):
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
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) >= 0:
            for i in range(ranges[0], ranges[1] + 1):
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
        end_tag = ["1. Introduction", "1. introduction",
                   "Introduction", "introduction",
                   "1.", "摘要"]
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


if __name__ == "__main__":
    basic_config(logs_style=LOG_STYLE_PRINT)
    a = "E:\\git-code\\paper-crawler\\CVPR\\CVPR_2020\\1\\1"
    # write_file(path=local_path_generate(a, "1.txt"),
    #            mode="w+",
    #            string=get_para_from_pdf(a))
    write_file(path=local_path_generate(a, "2.txt"),
               mode="w+",
               string=text_translate(a + "\\1.txt"))
