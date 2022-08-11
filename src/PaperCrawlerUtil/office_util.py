# -*- coding: utf-8 -*-
# @Time    : 2022/8/7 15:52
# @Author  : 银尘
# @FileName: office_util.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
import csv
from common_util import *
from crawler_util import verify_rule


class CsvProcess:

    def __init__(self, file_path: str = "", encoding: str = "utf-8-sig", open_mode: str = "r") -> None:
        super().__init__()
        self.encoding = encoding
        self.mode = open_mode
        self.path = file_path
        self.size = self.csv_size()

    def csv_size(self):
        try:
            with open(self.path, mode=self.mode, encoding=self.encoding) as f:
                self.size = len(f.readlines())
            f.close()
        except Exception as e:
            log("文件打开异常：{}".format(e))
        return self.size

    def csv_data(self, data_format: str = "list") -> List[List] or List[dict]:
        res = []
        try:
            with open(self.path, mode=self.mode, encoding=self.encoding) as f:
                if data_format == "list":
                    reader = csv.reader(f)
                else:
                    reader = csv.DictReader(f)
                for row in reader:
                    res.append(row)
            f.close()
            return res
        except Exception as e:
            log("异常：{}".format(e))
            return res
        return res

    def write_csv(self, data: List[List] or List[dict], data_format: str = "list", write_path: str = "",
                  title: List[str] = None) -> bool:
        if verify_rule(rule={0: LESS_THAN_AND_EQUAL}, origin=len(write_path)):
            write_path = local_path_generate("", suffix=".csv")
        try:
            with open(write_path, mode="w+", encoding=self.encoding) as f:
                if data_format == "list":
                    writer = csv.writer(f)
                else:
                    if title is None:
                        log("dict 方式需要提供表头", print_file=sys.stderr)
                        return False
                    writer = csv.DictWriter(f, title)
                    writer.writeheader()
                writer.writerows(data)
            f.close()
            return True
        except Exception as e:
            log("异常：{}".format(e))
            return False
        return False
