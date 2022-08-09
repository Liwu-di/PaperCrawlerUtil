# -*- coding: utf-8 -*-
# @Time    : 2022/8/7 15:48
# @Author  : 银尘
# @FileName: pdf_util.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
import io
import os

from PaperCrawlerUtil import verify_rule
from common_util import *
import pdfplumber
from PyPDF2 import PdfFileWriter, PdfFileReader
from pdf2docx import Converter


def pdf2docx(pdf_path: str, word_path: str, end_pages: int = None,
             start_pages: str = None, need_log: bool = True) -> None:
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
                log(string="转换失败文件{},{}".format(ele, e), print_file=sys.stderr)
            finally:
                cv.close()


def get_para_from_one_pdf(path: str, begin_tag: list = None,
                          end_tag: list = None, ranges: tuple = (0, 1)) -> str:
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
        log(string="打开PDF异常：{}".format(e), print_file=sys.stderr)
        return txt


def get_para_from_pdf(path: str, begin_tag: list = None, end_tag: list = None, ranges: tuple = (0, 1),
                      split_style: str = "===", valid_threshold: int = 0, need_log: bool = True) -> str:
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
                log(string="抽取文件疑似失败：{}".format(ele), print_file=sys.stderr)
            sum_count = sum_count + 1
        else:
            sum_count = sum_count + 1
            log(string="错误：{}不是PDF文件".format(ele), print_file=sys.stderr)
    log("总计抽取了文件数量：{}，其中有效抽取（>{}）数量：{}".format(sum_count, valid_threshold, valid_count))
    return txt


def getAllFiles(target_dir: str) -> list:
    """
    遍历文件夹
    :param target_dir: 遍历的文件夹
    :return: 所有文件的名称
    """
    files = []
    if len(target_dir) == 0:
        log(string="文件路径为空", print_file=sys.stderr)
        return files
    try:
        listFiles = os.listdir(target_dir)
    except Exception as e:
        log(string="打开文件夹{}异常：{}".format(target_dir, e), print_file=sys.stderr)
        return files
    for i in range(0, len(listFiles)):
        path = os.path.join(target_dir, listFiles[i])
        if os.path.isdir(path):
            files.extend(getAllFiles(path))
        elif os.path.isfile(path):
            files.append(path)
    return files


class sub_func_write_pdf(threading.Thread):

    def __init__(self, out_path: str, out_stream: io.BufferedWriter, out_pdf: PdfFileWriter) -> None:
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
            log(string=threading.currentThread().getName() + "写PDF出现异常：{}".format(e), print_file=sys.stderr)
            self.res = False

    def getRes(self):
        return self.res

    def raiseException(self):
        raise ThreadStopException()


def getSomePagesFromOnePDF(path: str, out_path: str, page_range: tuple or list,
                           need_log: bool = True, timeout: float = 20) -> bool:
    """
        从给定的文件路径中，截取指定的页面，保存到给定输出目录中
        :param path: 文件夹或者文件路径
        :param page_range: 截取的范围，如果是元组，则连续截取[a,b]的页面，注意从0开始，如果是列表，
        则按照列表给出的信息截取
        :param out_path:指定输出的目录
        :param need_log: 是否需要打印日志
        :param timeout: 线程结束时间，防止转换过程中，线程无意义等待
        :return: 返回布尔值，True表示成功转换
        """

    if len(path) == 0:
        log(string="路径参数为空，返回错误", print_file=sys.stderr)
        return False
    if type(page_range) != tuple and type(page_range) != list:
        log(string="页码范围有误，返回错误", print_file=sys.stderr)
        return False
    output = None
    pdf_file = None
    pdf_pages_len = None
    try:
        output = PdfFileWriter()
        pdf_file = PdfFileReader(open(path, "rb"))
        pdf_pages_len = pdf_file.getNumPages()
    except Exception as e:
        log(string="打开文件异常：{}".format(e), print_file=sys.stderr)
        return False
    iters = None
    if type(page_range) == tuple:
        new_page_range = ()
        for k in page_range:
            '''@todo: 完善verify_rule()'''
            if not (0 <= k <= pdf_pages_len - 1):
                log(string="范围参数有错", print_file=sys.stderr)
                return False
        if len(page_range) == 0:
            log(string="页码范围不明确，返回错误", print_file=sys.stderr)
            return False
        elif len(page_range) == 1:
            log("使用范围截取，但只有一个参数，结束参数默认为最大值")
            new_page_range = (page_range[0], pdf_pages_len - 1)
        elif len(page_range) > 2:
            log("使用范围参数，但参数数量过多，截取两个")
            new_page_range = (page_range[0], page_range[1])
        else:
            new_page_range = (page_range[0], page_range[1])
        iters = range(new_page_range[0], new_page_range[1])
    else:
        # 去重
        page_range = list(set(page_range))
        for k in page_range:
            '''@todo: 完善verify_rule()'''
            if not (0 <= k <= pdf_pages_len - 1):
                log(string="范围参数有错", print_file=sys.stderr)
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
                log(string=e, print_file=sys.stderr)
        if need_log or not success:
            log(("从文件{}截取页面到{}成功".format(path, out_path)) if success else ("从文件{}截取页面到{}失败".format(path, out_path)))
        return True
    except Exception as e:
        log(string="写文件出错：{}".format(e), print_file=sys.stderr)
        return False
    finally:
        pdf_file.stream.close()


def getSomePagesFromFileOrDirectory(path: str, page_range: tuple or list, out_directory: str = "",
                                    need_log: bool = True, timeout: float = 20, need_bar: bool = True) -> None:
    """
    从给定的文件夹或者文件路径中，截取指定的页面，保存到给定输出目录中
    :param need_bar: 是否需要使用进度条代替日志显示，此项为True时，覆盖need_log参数
    :param path: 文件夹或者文件路径
    :param page_range: 截取的范围，如果是元组，则连续截取[a,b]的页面，注意从0开始，如果是列表，
    则按照列表给出的信息截取
    :param out_directory:指定输出的目录
    :param need_log: 是否需要打印日志
    :param timeout: 线程结束时间，防止转换过程中，线程无意义等待
    :return:
    """

    count = 0
    sum = 0
    need_log = need_log if not need_bar else False
    if os.path.isfile(path):
        p = process_bar(total=1, desc="文件截取进度：", final_prompt="文件截取完成")
        p.process(0, 1, 1)
        sum = 1
        if getSomePagesFromOnePDF(path, local_path_generate(out_directory, need_log=need_log), page_range, need_log):
            count = count + 1
            p.process(1, 1, 1)
    else:
        files = getAllFiles(path)
        total = 0
        for f in files:
            if f.endswith(".pdf"):
                total = total + 1
        p = process_bar(total=total, desc="文件截取进度：", final_prompt="文件截取完成")
        p.process(0, 1, total)
        for k in files:
            if not k.endswith(".pdf"):
                log(string="文件{}不是PDF文件".format(k), print_file=sys.stderr)
                continue
            sum = sum + 1
            if getSomePagesFromOnePDF(k, local_path_generate(out_directory, need_log=need_log), page_range, need_log,
                                      timeout):
                count = count + 1
                p.process(count, 1, total)
    if need_log:
        log("总计待截取文件：{}，成功：{}".format(str(sum), str(count)))


def cooperatePdfWithLimit(files: list, page_range: tuple or list = None, out_path: str = "",
                          need_log: bool = True, timeout: float = -1, group_id: str = "",
                          need_group: bool = True) -> bool:
    """
    合并列表的PDF文件到指定目录
    :param files: 文件列表
    :param page_range: 合并的页码范围，如果是元组，则连续截取[a,b]的页面，注意从0开始，如果是列表，
    则按照列表给出的信息截取
    :param out_path: 输出文件的目录，如果不给定则默认自动生成
    :param need_log: 是否需要日志
    :param timeout: 线程等待时间，如果该值为-1则一直等到线程执行完毕，否则等待时间间隔之后，将结束线程，
    未合并完成的文件则自动失败
    :param group_id: 分组号，会自动添加在给定的文件名上，如果给定目标文件名为空，则自动生成文件名
    :param need_group: 是否需要分组
    :return:
    """
    output = None
    if need_group:
        out_path = list(out_path)
        temp = []
        for p in range(len(out_path) - 4):
            temp.append(out_path[p])
        out_path = "".join(temp)
        out_path = (out_path + group_id + ".pdf") if len(out_path) != 0 else local_path_generate("")
    else:
        out_path = out_path if len(out_path) != 0 else local_path_generate("")
    count = 0
    try:
        output = PdfFileWriter()
    except Exception as e:
        log(string="打开PDF写文件工具失败：{}".format(e), print_file=sys.stderr)
    file_readers = []
    for file in files:
        reader = None
        if not file.endswith(".pdf"):
            log(string="文件{}不是PDF文件，略过".format(file), print_file=sys.stderr)
            continue
        try:
            if file == out_path:
                continue
            reader = PdfFileReader(open(file, "rb"))
        except Exception as e:
            log(string="打开文件{}失败{}".format(file, e), print_file=sys.stderr)
            continue
        pdf_pages_len = reader.getNumPages()
        iters = None
        if type(page_range) == tuple:
            new_page_range = ()
            if len(page_range) == 0:
                if need_log:
                    log("默认全部合并，因为范围为空")
                new_page_range[0] = 0
                new_page_range[1] = pdf_pages_len - 1
            elif len(page_range) == 1:
                if need_log:
                    log("使用范围截取，但只有一个参数，结束参数默认为最大值")
                new_page_range = (page_range[0], pdf_pages_len - 1)
            elif len(page_range) > 2:
                if need_log:
                    log("使用范围参数，但参数数量过多，截取两个")
                new_page_range = (page_range[0], page_range[1])
            else:
                new_page_range = (page_range[0], page_range[1])
            iters = range(new_page_range[0], new_page_range[1])
        else:
            page_range = list(set(page_range))
            for k in page_range:
                try:
                    if not (verify_rule({0: GREATER_AND_EQUAL, pdf_pages_len - 1: LESS_THAN_AND_EQUAL}, float(k))):
                        log(string="范围参数有错", print_file=sys.stderr)
                        return False
                except Exception as e:
                    log(string="参数范围输入格式错误：{}".format(e), print_file=sys.stderr)
                    return False
            iters = page_range
        for i in iters:
            output.addPage(reader.getPage(i))
        file_readers.append(reader)
        count = count + 1
    try:
        outputStream = open(out_path, "wb")
    except Exception as e:
        log(string="打开文件异常：{}".format(e), print_file=sys.stderr)
        return False
    sub = sub_func_write_pdf(out_path, outputStream, output)
    # sub.setDaemon(True)
    sub.start()
    if timeout < 0:
        sub.join()
    else:
        sub.join(timeout=timeout)
    flag = sub.getRes()
    try:
        sub.raiseException()
    except ThreadStopException as e:
        if need_log:
            log("结束线程")
    for read in file_readers:
        read.stream.close()
    if flag:
        if need_log:
            log("合并文件到{}成功，共计{}文件，合并总数{}".format(out_path, str(len(files)), str(count)))
        return True
    else:
        log(string="合并失败", print_file=sys.stderr)
        return False


def cooperatePdf(path: str, page_range: tuple or list = None, out_path: str = "",
                 need_log: bool = True, timeout: float = -1, group_number: int = 50,
                 need_group: bool = True, need_processbar: bool = True) -> None:
    """
    合并文件夹中所有的PDF文件到指定目录
    :param need_processbar: 是否需要使用进度条代替日志显示，此项为True时，覆盖need_log参数
    :param path: 文件夹路径
    :param page_range: 合并的页码范围，如果是元组，则连续截取[a,b]的页面，注意从0开始，如果是列表，
    则按照列表给出的信息截取，如果此项值不给定，则默认全部合并
    :param out_path: 输出文件的目录，如果不给定则默认自动生成
    :param need_log: 是否需要日志
    :param timeout: 线程等待时间，如果该值为-1则一直等到线程执行完毕，否则等待时间间隔之后，将结束线程，
    未合并完成的文件则自动失败
    :param group_number: 分组时每组的合并数量
    :param need_group: 是否需要分组合并
    :return:
    """
    need_log = need_log if not need_processbar else False
    if len(path) == 0:
        log("给定路径为空，合并结束：{}".format(path))
    elif os.path.isfile(path):
        log("给定的是文件路径，合并结束：{}".format(path))
    if page_range is None:
        page_range = []
    files = getAllFiles(path)
    if need_group:
        if need_processbar:
            p = process_bar(desc="文件合并进度：", total=len(files), final_prompt="文件合并完成")
            p.process(0, group_number, len(files))
        i: int = 0
        group_id: int = 0
        file_group = []
        while i < len(files):
            if (i != 0 and ((i % group_number) == 0)) or (i == len(files) - 1):
                cooperatePdfWithLimit(file_group, page_range, out_path, need_log, timeout, str(group_id))
                group_id = group_id + 1
                file_group.clear()
                if need_processbar:
                    p.process(0, group_number, len(files))
            file_group.append(files[i])
            i = i + 1
    else:
        if need_processbar:
            p = process_bar(desc="文件合并进度：", total=len(files), final_prompt="文件合并完成")
            p.process(0, group_number, len(files))
        cooperatePdfWithLimit(files, page_range, out_path, need_log, timeout, need_group=False)
        if need_processbar:
            p.process(0, len(files), len(files))