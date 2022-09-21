# -*- coding: utf-8 -*-
# @Time    : 2022/8/7 15:52
# @Author  : 银尘
# @FileName: office_util.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
import csv

import xlrd
import xlwt

from PaperCrawlerUtil.common_util import *
from PaperCrawlerUtil.crawler_util import verify_rule


class CsvProcess:

    def __init__(self, file_path: str = "", encoding: str = "utf-8-sig", open_mode: str = "r") -> None:
        """
        CSV处理初始化
        :param file_path:csv文件地址
        :param encoding: 打开csv的编码，一般默认即可，
        :param open_mode: 打开模式，默认即可
        """
        super().__init__()
        self.encoding = encoding
        self.mode = open_mode
        self.path = file_path

    def csv_size(self):
        """
        csv文件的行数
        :return:
        """
        try:
            with open(self.path, mode=self.mode, encoding=self.encoding) as f:
                self.size = len(f.readlines())
            f.close()
        except Exception as e:
            log("文件打开异常：{}".format(e))
        return self.size

    def csv_data(self, data_format: str = "list") -> List[List] or List[dict]:
        """
        返回csv的全部数据，可以选择返回的格式
        :param data_format: list or dict，如果为list，则返回：[[],[], ...]
        否则返回[{}, {}, ...]
        :return:
        """
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
        """
        写csv文件，这个除了用到初始化的encoding，其余都没有用到
        :param data: 需要写入的数据，格式为[[],[], ...]或者[{}, {}, ...]
        :param data_format: 数据的格式，list or dict
        :param write_path: 写入的路径，默认自动生成
        :param title: 可选参数，如果为dict方式写入，需要提供表头，格式为[a, b, ...]
        :return:
        """
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

    def __init__(self, filename: str = "", sheet_index: int = 0, sheet_name: str = None) -> None:

        """
        只能处理xls文件，后续进行改造
        :param filename: 文件名以及路径，如果路径或者文件名有中文给前面加一个 r
        :param sheet_index: 工作簿序号
        :param sheet_name: 工作簿名称，这个优先级最高
        """
        super().__init__()
        self.filename = filename
        self.sheet_index = sheet_index
        self.sheet_name = sheet_name
        if len(filename) > 0:
            self.excel = xlrd.open_workbook(filename)
            self.sheet_names = self.excel.sheet_names()
            self.sheet = self.excel.sheet_by_name(sheet_name) \
                if sheet_name is not None else self.excel.sheet_by_index(sheet_index)
            self.row_size = self.sheet.nrows
            self.col_size = self.sheet.ncols
        else:
            self.excel = None
            self.sheet_names = []
            self.sheet = None
            self.row_size = 0
            self.col_size = 0

    def modify(self, sheet_index: int = None, sheet_name: str = None, file_name:str = None):
        """
        修改初始化参数
        :param file_name: 文件名
        :param sheet_index: 工作簿序号
        :param sheet_name: 工作簿名称，这个优先级最高
        :return:
        """
        self.filename = file_name if file_name is not None else self.filename
        if len(self.filename) > 0:
            self.excel = xlrd.open_workbook(self.filename)
            self.sheet_names = self.excel.sheet_names()
            self.sheet = self.excel.sheet_by_name(sheet_name) \
                if sheet_name is not None else self.excel.sheet_by_index(sheet_index)
            self.row_size = self.sheet.nrows
            self.col_size = self.sheet.ncols
        self.sheet_index = sheet_index if sheet_index is not None else self.sheet_index
        self.sheet_name = sheet_name if sheet_name is not None else self.sheet_name
        if sheet_index is not None or sheet_name is not None:
            self.sheet = self.excel.sheet_by_name(sheet_name) \
                if sheet_name is not None else self.excel.sheet_by_index(sheet_index)
            self.row_size = self.sheet.nrows
            self.col_size = self.sheet.ncols

    def excel_data(self, process_format: str = ROW, param_range: tuple = (0, None),
                   return_type: str = EXCEL_RETURN_TYPE[LIST_OF_VALUE], index: int = 0):
        """
        读取excel数据
        :param process_format: 按行或者列或者单元格处理数据，参数[ROW, COL, CELL]
        :param param_range: 如果为行模式，则表示列的范围，如果为列模式则为行的范围，单元格则为坐标
        :param return_type: 返回数据的类型，参考EXCEL_RETURN_TYPE，可以返回对象，类型，值，长度
        :param index: 处理行或者列的时候，选择处理哪一行或者列
        :return:
        """
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
        """
        检测工作簿是否加载完毕
        :return:
        """
        return self.excel.sheet_loaded(self.sheet_name if self.sheet_name is not None else self.sheet_index)

    def write_excel(self, content: List[List[object]], path: str, book_name: str = "new book",
                    encoding: str = "ascii"):
        """
        @todo: 这里数据的格式重新调整一次，做成可以写多个工作簿的
        写excel文件，注意不能超过256列
        :param content: 写入的数据，格式为[[], [], ...]，每一个列表代表一行数据
        :param path: 写入的路径
        :param book_name: 工作簿的名称
        :param encoding: 编码，默认ascii
        :return:
        """
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
        if self.excel is not None:
            self.excel.release_resources()


if __name__ == "__main__":
    excel = ExcelProcess()
    excel.write_excel([[1, 2], [3, 4]], local_path_generate("", suffix=".xls"))
