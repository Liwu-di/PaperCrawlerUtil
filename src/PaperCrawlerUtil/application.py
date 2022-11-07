# -*- coding: utf-8 -*-
# @Time    : 2022/9/5 16:50
# @Author  : 银尘
# @FileName: application.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
import argparse
import ast
import json
from PaperCrawlerUtil.common_util import *
from flask import Flask, request
from PaperCrawlerUtil.constant import *
from PaperCrawlerUtil.research_util import *
"""
this file is some applications constructed by PaperCrawlerUtil 
and can run by Flask and provide services to website
"""

applications = Flask(__name__)


@applications.route("/")
def hello_world():
    return 'hello world'


@applications.route("/code_generate/", methods=[POST])
def generate():
    data = json.loads(request.get_data())
    # 到最终保存或提取文件需要多少层
    layer = data['layer']
    # rule， 爬取链接之后，需要根据这个条件抽取元素，每层一个
    rule = data['rule']
    element = data['element']
    url_pre = data["url_pre"]
    ele_split = data["ele_split"]
    file_directory = data["file_directory"]
    url = data["url"]
    imports = "from PaperCrawlerUtil.common_util import * \n from PaperCrawlerUtil.crawler_util import * \nfrom PaperCrawlerUtil.document_util import *\n\n"
    config = "basic_config(logs_style=LOG_STYLE_PRINT, require_proxy_pool=True, need_tester_log=False, need_getter_log=False)\n"
    body = ""
    for l in range(int(layer)):
        body = body + get_split(lens=l, style="   ") + "html_" + str(l) + " = " + "random_proxy_header_access(\"" + url + "\"," + ")\n"
        body = body + get_split(lens=l, style="   ") + "attr_list_" + str(l) + " = get_attribute_of_html(html_" + str(l) + ", " + str(rule[l]) + ")\n"
        body = body + get_split(lens=l, style="   ") + "for ele_" + str(l) + " in attr_list_"+ str(l) +":\n"
        body = body + get_split(lens=l+1, style="   ") + "path_" + str(l) + " = ele_" + str(l) + ".split(\"" + ele_split[2 * l] +"\")[1].split(\"" + ele_split[2 * l + 1] + "\")[0]\n"
    code = imports + config + body
    return code


@applications.route("/get_record/", methods=[POST])
def get_record():
    """
    查询research结果记录
    :return:
    """
    data = json.loads(request.get_data())
    c = ast.literal_eval(data["c"])
    page = data["page"]
    no = data["no"]
    record = ResearchRecord(**c)
    data = {"data": list(record.select_page(page, no)), "code": 0}
    return json.encoder.JSONEncoder().encode(data).replace("\n", "")


@applications.route("/export_research_record/", methods=[POST])
def export_research_record():
    """
    导出research结果记录
    :return:
    """
    data = json.loads(request.get_data())
    range = ast.literal_eval(data["range"])
    c = ast.literal_eval(data["c"])
    record = ResearchRecord(**c)
    res = record.export(id_range=range, file_type="xls")
    data = {"data": str(res), "code": 0}
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000, help="port number will be used to start")
    args = parser.parse_args()
    applications.run(host="0.0.0.0", port=args.port, debug=True)
