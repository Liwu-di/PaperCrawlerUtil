# -*- coding: utf-8 -*-
# @Time    : 2023/5/29 16:42
# @Author  : 银尘
# @FileName: log_util.py
# @Software: PyCharm
# @Email   : liwudi@liwudi.fun
# @Info    : utils for logging
import logging
import smtplib
import sys
from email.mime.text import MIMEText
from email.utils import formataddr

import tqdm
import PaperCrawlerUtil.global_val as global_val
from PaperCrawlerUtil.constant import *


def write_log(string: str = "", print_file: object = sys.stdout, func: callable = None):
    if func is not None:
        func(string)
    else:
        if print_file == sys.stdout:
            logging.warning(string)
        else:
            logging.error(string)


def log(*string: str or object, print_sep: str = ' ', print_end: str = "\n", print_file: object = sys.stdout,
        print_flush: bool = None, need_time_stamp: bool = True, is_test_out: bool = False,
        funcs: callable = None, level: str = None) -> bool:
    """
    本项目的通用输出函数， 使用这个方法可以避免tqdm进度条被中断重新输出
    :param level: 日志等级
    :param funcs: 日志输出函数
    :param is_test_out: 是否是测试输出，正式场合不需要输出，可以通过common_util.basic_config()控制
    :param need_time_stamp: 是否需要对于输出的日志添加时间戳
    :param string: 待输出字符串或者对象，对象只支持print方式或者可以被str函数转成字符串的对象
    :param print_sep: 输出字符串之间的连接符，同print方法sep，目前被废弃
    :param print_end: 输出字符串之后的结尾添加字符
    :param print_file: 输出流
    :param print_flush: 是否强制输出缓冲区，同print方法flush，目前被废弃
    :return:
    """
    global log_style
    flag = True
    print_file = global_val.get_value(KEEP_PROCESS_BAR_STYLE_FILE) \
        if global_val.get_value(KEEP_PROCESS_BAR_STYLE) else print_file
    is_test_model = global_val.get_value(IS_LOG_TEST_MODE) \
        if global_val.get_value(IS_LOG_TEST_MODE) else False
    if is_test_out and (not is_test_model):
        return flag
    global_log_level = global_val.get_value(GLOBAL_LOG_LEVEL)
    s = ""
    try:
        for k in string:
            s = s + str(k) + print_sep
    except Exception as e:
        s = "待输出的列表中含有无法转换为字符串的值，{}".format(e)
        try:
            print(string, file=print_file, end=print_end, sep=print_sep, flush=print_flush)
        except Exception as e:
            s = "待输出的日志不是字符串形式，也无法使用print方式显示，{}".format(e)
            flag = False
    if need_time_stamp and type(s) == str:
        s = get_timestamp(split=["-", "-", " ", ":", ":"]) + get_split(lens=3, style=" ") + s
    if log_style == LOG_STYLE_LOG:
        write_log(s, print_file, func=funcs)
    elif log_style == LOG_STYLE_PRINT:
        if (LEVEL2NUM[global_log_level] if type(global_log_level) == str else global_log_level) <= \
                (LEVEL2NUM[level] if type(level) == str else level):
            tqdm.write(s=s, file=print_file, end=print_end)
    elif log_style == LOG_STYLE_ALL:
        if (LEVEL2NUM[global_log_level] if type(global_log_level) == str else global_log_level) <= \
                (LEVEL2NUM[level] if type(level) == str else level):
            write_log(s, print_file, func=funcs)
            tqdm.write(s=s, file=print_file, end=print_end)
    return flag


def send_email(sender_email, sender_password, receiver_email,
               message, subject="default subject"):
    """
    send email
    :param sender_email:
    :param sender_password:
    :param receiver_email:
    :param message:
    :param subject:
    :return:
    """
    try:
        if sender_email.endswith('@163.com'):
            smtp_server = 'smtp.163.com'
            smtp_port = SMTP_URL_163MAIL
        elif sender_email.endswith('@qq.com'):
            smtp_server = 'smtp.qq.com'
            smtp_port = SMTP_URL_QQMAIL
        else:
            Logs.log_error('Unsupported email domain')

        msg = MIMEText(message, 'plain', 'utf-8')
        msg['From'] = formataddr(('Sender', sender_email))
        msg['To'] = formataddr(('Receiver', receiver_email))
        msg['Subject'] = subject

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [receiver_email], msg.as_string())

        Logs.log_info('Email sent successfully!')
    except Exception as e:
        Logs.log_error('Error sending email:', str(e))


class Logs(object):

    def __init__(self, sender_email, sender_password, receiver_email):
        super().__init__()
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.receiver_email = receiver_email

    class LOG(object):

        def __init__(self, ):
            super().__init__()

        @staticmethod
        def log_info(string, *args, **keywords):
            logging.info(string, *args, **keywords)

        @staticmethod
        def log_warning(string, *args, **keywords):
            logging.warning(string, *args, **keywords)

        @staticmethod
        def log_error(string, *args, **keywords):
            logging.error(string, *args, **keywords)

        @staticmethod
        def log_debug(string, *args, **keywords):
            logging.debug(string, *args, **keywords)

        @staticmethod
        def log_email(sender_email, sender_password, receiver_email,
                      message, subject="default subject"):
            sender_email(sender_email, sender_password, receiver_email,
                         message, subject="default subject")

        def getMethod(self, funcs):
            return getattr(self, funcs, self.log_warning)

    @staticmethod
    def log(*string: str or object, print_sep: str = ' ', print_end: str = "\n",
            print_file: object = sys.stdout,
            print_flush: bool = None, need_time_stamp: bool = True, level: str = INFO, is_test_out: bool = False,
            **email_param):
        func_factory = Logs.LOG()
        funcs = func_factory.getMethod("log_" + level)
        log(*string, print_sep=print_sep, print_end=print_end, print_file=print_file, print_flush=print_flush,
            need_time_stamp=need_time_stamp, is_test_out=is_test_out, funcs=funcs, level=level, **email_param)

    @staticmethod
    def log_warn(*string: str or object, print_sep: str = ' ', print_end: str = "\n",
                 print_file: object = sys.stdout,
                 print_flush: bool = None, need_time_stamp: bool = True):
        Logs.log(*string, print_sep=print_sep, print_end=print_end, print_file=print_file, print_flush=print_flush,
                 need_time_stamp=need_time_stamp, is_test_out=False, level=WARN)

    @staticmethod
    def log_info(*string: str or object, print_sep: str = ' ', print_end: str = "\n",
                 print_file: object = sys.stdout,
                 print_flush: bool = None, need_time_stamp: bool = True):
        Logs.log(*string, print_sep=print_sep, print_end=print_end, print_file=print_file, print_flush=print_flush,
                 need_time_stamp=need_time_stamp, is_test_out=False, level=INFO)

    @staticmethod
    def log_debug(*string: str or object, print_sep: str = ' ', print_end: str = "\n",
                  print_file: object = sys.stdout,
                  print_flush: bool = None, need_time_stamp: bool = True):
        Logs.log(*string, print_sep=print_sep, print_end=print_end, print_file=print_file, print_flush=print_flush,
                 need_time_stamp=need_time_stamp, is_test_out=False, level=DEBUG)

    @staticmethod
    def log_error(*string: str or object, print_sep: str = ' ', print_end: str = "\n",
                  print_file: object = sys.stdout,
                  print_flush: bool = None, need_time_stamp: bool = True):
        Logs.log(*string, print_sep=print_sep, print_end=print_end, print_file=print_file, print_flush=print_flush,
                 need_time_stamp=need_time_stamp, is_test_out=False, level=ERROR)

    def log_email(self, message, subject="default subject"):
        send_email(sender_email=self.sender_email, sender_password=self.sender_password,
                   receiver_email=self.receiver_email, message=message, subject=subject)
