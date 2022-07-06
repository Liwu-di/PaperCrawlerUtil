import hashlib
import http
import io
import json
import threading
import urllib
from typing import Optional, Callable, Any, Iterable, Mapping

import PyPDF2
from PyPDF2 import PdfFileWriter, PdfFileReader
import pdfplumber
from googletrans import Translator
from pdf2docx import Converter

from crawler_util import *


def baidu_translate(string,
                    appid,
                    secret_key,
                    src="auto",
                    dst="zh",
                    sleep_time=1.2,
                    need_log=True):
    """
    百度翻译
    :param need_log: 是否需要日志
    :param string:
    :param appid:
    :param secret_key:
    :param src:
    :param dst:
    :param sleep_time:
    :return:
    """
    if need_log:
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


def google_translate(string, src='en', dest='zh-cn', proxies=None, sleep_time=1.2, need_log=True):
    """
    谷歌翻译
    @todo 提供一个源语言和目的语言的表
    :param need_log: 是否需要日志
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
    if need_log:
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


def sentence_translate(string, appid, secret_key, max_retry=10, proxies=None, probability=0.5, is_google=True):
    """
    随机使用百度谷歌翻译句子
    :param string: 待翻译语句
    :param appid: 百度翻译appid
    :param secret_key: 百度翻译密钥
    :param max_retry: 最大尝试次数
    :param proxies: 代理
    :param probability: 百度和谷歌翻译之间使用的比例，这个值趋向1则使用谷歌翻译概率大，否则使用百度翻译概率大
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
    :param proxies: 代理，样例 proxies = {"https": SyncHTTPProxy((b'http', b'127.0.0.1', 33210, b'')),
               "http": SyncHTTPProxy((b'http', b'127.0.0.1', 33210, b''))}
    :param probability:百度和谷歌翻译之间使用的比例，这个值趋向1则使用谷歌翻译概率大，否则使用百度翻译概率大
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


def pdf2docx(pdf_path, word_path, end_pages=None, start_pages=None, need_log=True):
    """
    转换pdf 到word文件，可以自动识别是文件夹还是单个文件，其中word_path表示的生成的word的文件夹，不论是
    单个还是文件夹批量转换，这个值都是文件夹
    :param need_log: 是否需要日志
    :param pdf_path: pdf的路径
    :param word_path: 用于存放word的路径，必须是文件夹路径
    :param end_pages: 结束页码
    :param start_pages: 开始页码
    :return:
    """
    file_list = []
    file = True
    count = 0
    if os.path.isfile(pdf_path) and os.path.isfile:
        file_list.append(pdf_path)
        if need_log:
            log("转换文件{}开始".format(pdf_path))
    else:
        file_list.extend(getAllFiles(pdf_path))
        if need_log:
            log("获取文件夹{}文件成功".format(pdf_path))
        file = False
    for ele in file_list:
        if ele.endswith(".pdf"):
            try:
                cv = Converter(ele)
                if start_pages is None:
                    start_pages = 0
                if end_pages is None:
                    end_pages = len(cv.pages)
                if not file:
                    cv.convert(local_path_generate(word_path), start=start_pages, end=end_pages)
                else:
                    cv.convert(local_path_generate(word_path, suffix=".docx"), start=start_pages, end=end_pages)
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


def get_para_from_pdf(path, begin_tag=None, end_tag=None, ranges=(0, 1),
                      split_style="===", valid_threshold=0, need_log=True):
    """
    用来从pdf文件中获取一些文字，可以通过设置开始或者结束标志，以及页码范围获取自己想要的内容
    如果是文件夹，则直接遍历文件夹中所有的PDF，返回所有符合的字符串，同时可以设置分隔符
    :param need_log: 是否需要日志
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
                if need_log:
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


class sub_func_write_pdf(threading.Thread):

    def __init__(self, out_path: str, out_stream: io.BufferedWriter, out_pdf) -> None:
        threading.Thread.__init__(self)
        self.res = False
        self.out_path = out_path
        self.out_stream = out_stream
        self.output = out_pdf

    def run(self) -> None:
        super().run()
        try:
            self.output.write(self.out_stream)
            self.res = True
            self.out_stream.close()
        except Exception as e:
            log(threading.currentThread().getName() + "写PDF出现异常：{}".format(e))
            self.res = False

    def getRes(self):
        return self.res

    def raiseException(self):
        raise Exception("终止线程")


def getSomePagesFromOnePDF(path, out_path, page_range: tuple or list, need_log=True, timeout: float = 20) -> bool:
    if len(path) == 0:
        log("路径参数为空，返回错误")
        return False
    if type(page_range) != tuple and type(page_range) != list:
        log("页码范围有误，返回错误")
        return False
    output = None
    pdf_file = None
    pdf_pages_len = None
    try:
        output = PdfFileWriter()
        pdf_file = PdfFileReader(open(path, "rb"))
        pdf_pages_len = pdf_file.getNumPages()
    except Exception as e:
        log("打开文件异常：{}".format(e))
        return False
    iters = None
    if type(page_range) == tuple:
        new_page_range = ()
        for k in page_range:
            '''@todo: 完善verify_rule()'''
            if not (0 <= k <= pdf_pages_len - 1):
                log("范围参数有错")
                return False
        if len(page_range) == 0:
            log("页码范围不明确，返回错误")
            return False
        elif len(page_range) == 1:
            log("使用范围截取，但只有一个参数，结束参数默认为最大值")
            new_page_range = (page_range[0], pdf_pages_len-1)
        elif len(page_range) > 2:
            log("使用范围参数，但参数数量过多，截取两个")
            new_page_range = (page_range[0], page_range[1])
        else:
            new_page_range = (page_range[0], page_range[1])
        iters = range(new_page_range[0], new_page_range[1])
    else:
        for k in page_range:
            '''@todo: 完善verify_rule()'''
            if not (0 <= k <= pdf_pages_len - 1):
                log("范围参数有错")
                return False
        iters = page_range
    for i in iters:
        output.addPage(pdf_file.getPage(i))
    try:
        outputStream = open(out_path, "wb")
        sub = sub_func_write_pdf(out_path, outputStream, output)
        sub.setDaemon(True)
        sub.start()
        sub.join(timeout=timeout)
        success = sub.getRes()
        try:
            sub.raiseException()
        except Exception as e:
            if need_log:
                log(e)
        if need_log or not success:
            log(("从文件{}截取页面到{}成功".format(path, out_path)) if success else ("从文件{}截取页面到{}失败".format(path, out_path)))
        return True
    except Exception as e:
        log("写文件出错：{}".format(e))
        return False


def getSomePagesFromFileOrDirectory(path, page_range: tuple or list, out_directory="", need_log: bool=True, timeout: float=20):
    count = 0
    sum = 0
    if os.path.isfile(path):
        sum = 1
        if getSomePagesFromOnePDF(path, local_path_generate(out_directory), page_range, need_log):
            count = count + 1
    else:
        files = getAllFiles(path)
        for k in files:
            if not k.endswith(".pdf"):
                log("文件{}不是PDF文件".format(k))
                continue
            sum = sum + 1
            if getSomePagesFromOnePDF(k, local_path_generate(out_directory), page_range, need_log, timeout):
                count = count + 1
    if need_log:
        log("总计待截取文件：{}，成功：{}".format(str(sum), str(count)))


if __name__ == "__main__":
    basic_config(logs_style=LOG_STYLE_PRINT)
