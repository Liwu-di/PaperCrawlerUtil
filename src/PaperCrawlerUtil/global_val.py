# -*- coding: utf-8 -*-
# @Time    : 2022/7/15 11:48
# @Author  : 银尘
# @FileName: global_val.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
import threading


modify_lock = threading.Lock()


def _init():  # 初始化
    global _global_dict
    _global_dict = {}


def set_value(key, value):
    """定义一个全局变量"""
    modify_lock.acquire()
    _global_dict[key] = value
    modify_lock.release()


def get_value(key):
    """获得一个全局变量，不存在则提示读取对应变量失败"""
    try:
        return _global_dict[key]
    except Exception as e:
        print('读取'+key+'失败:{}\r\n'.format(e))
