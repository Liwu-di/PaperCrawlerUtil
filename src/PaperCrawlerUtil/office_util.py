# -*- coding: utf-8 -*-
# @Time    : 2022/8/7 15:52
# @Author  : 银尘
# @FileName: office_util.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
import csv

import xlrd
import xlwt

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


class ExcelProcess:

    #@todo 只能打开xls，需要换库解决，xlrd新版本不行了

    def __init__(self, filename: str, sheet_index: int = 0, sheet_name: str = None) -> None:
        # 文件名以及路径，如果路径或者文件名有中文给前面加一个 r
        super().__init__()
        self.filename = filename
        self.sheet_index = sheet_index
        self.sheet_name = sheet_name
        self.excel = xlrd.open_workbook(filename)
        self.sheet_names = self.excel.sheet_names()
        self.sheet = self.excel.sheet_by_name(sheet_name) \
            if sheet_name is not None else self.excel.sheet_by_index(sheet_index)
        self.row_size = self.sheet.nrows
        self.col_size = self.sheet.ncols

    def modify(self, sheet_index: int = None, sheet_name: str = None):
        self.sheet_index = sheet_index if sheet_index is not None else self.sheet_index
        self.sheet_name = sheet_name if sheet_name is not None else self.sheet_name
        if sheet_index is not None or sheet_name is not None:
            self.sheet = self.excel.sheet_by_name(sheet_name) \
                if sheet_name is not None else self.excel.sheet_by_index(sheet_index)
            self.row_size = self.sheet.nrows
            self.col_size = self.sheet.ncols

    def excel_data(self, process_format: str = ROW, param_range: tuple = (0, None),
                   return_type: str = EXCEL_RETURN_TYPE[LIST_OF_VALUE], index: int = 0):
        if process_format not in [ROW, COL, CELL]:
            process_format = ROW
        if return_type not in [EXCEL_RETURN_TYPE[LIST_OF_TYPE], EXCEL_RETURN_TYPE[LIST_OF_VALUE],
                               EXCEL_RETURN_TYPE[LIST_OF_OBJECT], EXCEL_RETURN_TYPE[TYPE_OF_LENGTH]]:
            return_type = EXCEL_RETURN_TYPE[LIST_OF_VALUE]
        if process_format == ROW:
            if return_type == LIST_OF_OBJECT:
                return self.sheet.row_slice(index, param_range[0], param_range[1])
            elif return_type == LIST_OF_VALUE:
                return self.sheet.row_values(index, param_range[0], param_range[1])
            elif return_type == LIST_OF_TYPE:
                return self.sheet.row_types(index, param_range[0], param_range[1])
            elif return_type == TYPE_OF_LENGTH:
                return self.sheet.row_len(index)
        elif process_format == COL:
            if return_type == LIST_OF_OBJECT:
                return self.sheet.col_slice(index, param_range[0], param_range[1])
            elif return_type == LIST_OF_VALUE:
                return self.sheet.col_values(index, param_range[0], param_range[1])
            elif return_type == LIST_OF_TYPE:
                return self.sheet.col_types(index, param_range[0], param_range[1])
        elif process_format == CELL:
            if param_range[0] is None or param_range[1] is None:
                raise Exception("当为单元格模式时，param_range不能有None")
            if return_type == LIST_OF_OBJECT:
                return self.sheet.cell(param_range[0], param_range[1])
            elif return_type == LIST_OF_VALUE:
                return self.sheet.cell_value(param_range[0], param_range[1])
            elif return_type == LIST_OF_TYPE:
                return self.sheet.cell_type(param_range[0], param_range[1])

    def check_book_load_state(self):
        return self.excel.sheet_loaded(self.sheet_name if self.sheet_name is not None else self.sheet_index)

    def write_excel(self, content: List[List[object]], path: str, book_name: str = "new book",
                    encoding: str = "ascii"):
        # 创建新的workbook（其实就是创建新的excel）
        workbook = xlwt.Workbook(encoding=encoding)
        # 创建新的sheet表
        worksheet = workbook.add_sheet(book_name)
        # 往表格写入内容
        x = 0
        y = 0
        for k in content:
            for p in k:
                worksheet.write(x, y, p)
                y = y + 1
            x = x + 1
            y = 0
        # 保存
        workbook.save(path)

    def __del__(self):
        self.excel.release_resources()


