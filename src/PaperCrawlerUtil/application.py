# -*- coding: utf-8 -*-
# @Time    : 2022/9/5 16:50
# @Author  : 银尘
# @FileName: application.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
import argparse
import ast
import json
import sys

import global_val
from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.global_val import *
from flask import Flask, request
from PaperCrawlerUtil.constant import *
from PaperCrawlerUtil.research_util import *
"""
this file is some applications constructed by PaperCrawlerUtil 
and can run by Flask and provide services to website
"""

applications = Flask(__name__)

c = ""


def get_c(front_end_data: str = None) -> Dict:
    """
    获取数据库配置
    :return:
    """
    def translate(s: str) -> Dict:
        try:
            return ast.literal_eval(s)
        except Exception as e:
            log(e, print_file=sys.stderr)
            return {}
    if front_end_data is None or len(front_end_data) == 0:
        return translate(global_val.get_value("c"))
    else:
        return translate(front_end_data)

@applications.route("/")
def hello_world():
    return 'hello world'


@applications.route("/get_record/", methods=[POST])
def get_record():
    """
    查询research结果记录
    :return:
    """
    data = json.loads(request.get_data())
    c = get_c(data["c"])
    page = data["page"]
    no = data["no"]
    record = ResearchRecord(**c)
    data, page_sum = record.select_page(page, no)
    data = {"data": data, "sum": page_sum}
    data = generate_result(data=data)
    return json.encoder.JSONEncoder().encode(data).replace("\n", "")


@applications.route("/export_research_record/", methods=[POST])
def export_research_record():
    """
    导出research结果记录
    :return:
    """
    data = json.loads(request.get_data())
    range = ast.literal_eval(data["range"])
    c = get_c(data["c"])
    record = ResearchRecord(**c)
    res = record.export(id_range=range, file_type="xls")
    data = generate_result(data=str(res))
    return data


@applications.route("/delete_records/", methods=[POST])
def delete_records():
    """
    标记删除research结果记录
    :return:
    """
    data = json.loads(request.get_data())
    range = ast.literal_eval(data["range"])
    c = get_c(data["c"])
    record = ResearchRecord(**c)
    res = record.delete(range)
    data = generate_result(data=str(res))
    return data


@applications.route("/modify_records/", methods=[POST])
def modify_records():
    """
    修改research结果记录
    :return:
    """
    data = json.loads(request.get_data())
    c = get_c(data["c"])
    record = ResearchRecord(**c)
    res = record.modify(data)
    data = generate_result(data=str(res))
    return data


@applications.route("/get_by_id/", methods=[POST])
def get_by_id():
    """
    修改research结果记录
    :return:
    """
    data = json.loads(request.get_data())
    c = get_c(data["c"])
    record = ResearchRecord(**c)
    res = record.get_by_id(data)
    data = generate_result(data=str(res))
    return data


@applications.route("/search_pages/", methods=[POST])
def search_pages():
    """
    搜索分页查询
    :return:
    """
    data = json.loads(request.get_data())
    c = get_c(data["c"])
    record = ResearchRecord(**c)
    con = Conditions()
    con.add_condition("file_execute", "%" + data["search_field"] + "%", "like")
    con.add_condition("other", "%" + data["machine_code"] + "%", "like")
    con.add_condition("id", data["id_range_left"], ">=")
    con.add_condition("id", data["id_range_right"], "<=")
    if data.get("type") is not None:
        if data.get("type") == "delete":
            record.db_util.update(condition=con, kvs={"delete_flag": 1})
            return generate_result(data="True")
    else:
        res, sums = record.select_page_condition(conditions=con, page=1000)
        res = [list(i) for i in res]
        res = {"data": res}
        data = generate_result(data=res)
    return json.encoder.JSONEncoder().encode(data).replace("\n", "")


@applications.route("/insert_record/", methods=[POST])
def insert_record():
    """
    新增记录
    :return:
    """
    data = json.loads(request.get_data())
    c = get_c(data["c"])
    record = ResearchRecord(**c)
    record_id = record.insert(data["file"], data["exec_time"], data["args"])
    return generate_result(data=record_id)


@applications.route("/update_record/", methods=[POST])
def update_record():
    """
    更新记录
    :return:
    """
    data = json.loads(request.get_data())
    c = get_c(data["c"])
    record = ResearchRecord(**c)
    res = record.update(data["id"], data["finish_time"], data["result"], data["reamrk"])
    return generate_result() if res else generate_result(1, "failure")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000, help="port number will be used to start")
    parser.add_argument('--c', type=str, default="{}", help="access data base")
    args = parser.parse_args()
    global_val.set_value("c", args.c)
    applications.run(host="0.0.0.0", port=args.port, debug=False)
