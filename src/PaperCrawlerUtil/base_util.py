# -*- coding: utf-8 -*-
# @Time    : 2023/6/29 11:35
# @Author  : 银尘
# @FileName: base_util.py.py
# @Software: PyCharm
# @Email   : liwudi@liwudi.fun
# @Info    : the most base object or function
from PaperCrawlerUtil.constant import *
from bs4 import Tag
import time


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
            if type(origin) != float and type(origin) != int:
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


def get_timestamp(split: str or list = ["-", "-", " ", ":", ":"], accuracy: int = 6) -> str:
    """
    %Y  Year with century as a decimal number.
    %m  Month as a decimal number [01,12].
    %d  Day of the month as a decimal number [01,31].
    %H  Hour (24-hour clock) as a decimal number [00,23].
    %M  Minute as a decimal number [00,59].
    %S  Second as a decimal number [00,61].
    %z  Time zone offset from UTC.
    %a  Locale's abbreviated weekday name.
    %A  Locale's full weekday name.
    %b  Locale's abbreviated month name.
    %B  Locale's full month name.
    %c  Locale's appropriate date and time representation.
    %I  Hour (12-hour clock) as a decimal number [01,12].
    %p  Locale's equivalent of either AM or PM.
    :param split:
    :param accuracy:
    :return:
    """
    time_stamp_name = ["Y", "m", "d", "H", "M", "S", "z", "a", "A", "B", "c", "I", "p"]
    if accuracy >= len(time_stamp_name):
        accuracy = len(time_stamp_name)
    time_style = ""
    if type(split) == str:
        temp = split
        split = []
        for i in range(accuracy):
            split.append(temp)
    elif type(split) == list:
        if len(split) < accuracy:
            for i in range(accuracy - len(split)):
                split.append("-")
    for i in range(accuracy):
        if i == accuracy - 1:
            time_style = time_style + "%" + time_stamp_name[i]
        else:
            time_style = time_style + "%" + time_stamp_name[i] + split[i]
    return time.strftime(time_style, time.localtime())


def get_split(lens: int = 20, style: str = '=') -> str:
    """
    get a series of splits,like "======"
    :param lens: the length of split string
    :param style: the char used to create split string
    :return: a string of split
    """
    splits = ''
    lens = max(lens, 1)
    for i in range(lens):
        splits = splits + style
    return splits

