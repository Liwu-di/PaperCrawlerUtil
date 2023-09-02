# -*- coding: utf-8 -*-
# @Time    : 2022/10/21 16:39
# @Author  : 银尘
# @FileName: database_util.py
# @Software: PyCharm
# @Email   ：liwudi@liwudi.fun
import ast
import sys
import time
from typing import Callable, Dict, Tuple

from PaperCrawlerUtil.constant import *
from PaperCrawlerUtil.common_util import *
from sshtunnel import SSHTunnelForwarder
from PaperCrawlerUtil.document_util import *
import pymysql


class Conditions(dict):
    relations = ["=", ">", ">=", "<", "<=", "in", "not in", "like"]

    def __init__(self) -> None:
        super().__init__()

    def add_condition(self, key: str, value: str, relation: str = "="):
        self.__setitem__((key, value), relation)


class DB_util(object):
    """
    @todo:改为链接池或者提供连接池方式
    """

    def __init__(self, **db_conf) -> None:
        super().__init__()
        self.conn = None
        self.cursor = None
        self.ssl = None
        if len(db_conf) <= 0:
            log("需要配置字典", print_file=sys.stderr)
            return None
        check_ssl = True if db_conf.get("ssl_ip") is not None and db_conf.get("ssl_admin") is not None and \
                            db_conf.get("ssl_pwd") is not None and db_conf.get("ssl_db_port") is not None \
                            and db_conf.get("ssl_port") is not None else False
        if check_ssl:
            self.ssl = SSHTunnelForwarder(
                ssh_address_or_host=(db_conf.get("ssl_ip"), db_conf.get("ssl_port")),
                ssh_username=db_conf.get("ssl_admin"),
                ssh_password=db_conf.get("ssl_pwd"),
                remote_bind_address=('localhost', db_conf.get("ssl_db_port"))
            )
            self.ssl.start()
        self.db_url = "127.0.0.1" if check_ssl else db_conf.get("db_url")
        self.db_username = db_conf.get("db_username")
        self.db_pass = db_conf.get("pass")
        self.port = self.ssl.local_bind_port if check_ssl else db_conf.get("port")
        self.db_database = db_conf.get("db_database") if db_conf.get("db_database") is not None else "research"
        self.db_table = db_conf.get("db_table") if db_conf.get("db_table") is not None else "record_result"
        self.db_type = db_conf.get("db_type") if db_conf.get("db_type") is not None else "mysql"
        self.ignore_error = db_conf.get("ignore_error") if db_conf.get("ignore_error") is not None else True
        try:
            self.create_db_conn()
            self.cursor = self.conn.cursor()
        except Exception as e:
            log("链接数据库失败，请修改配置，云服务器请配置ssl：{}".format(e))
        self.show_sql = db_conf.get("show_sql") if db_conf.get("show_sql") is not None else True
        self.db_field = self.query_table_field()

    def generate_sql(self, kvs: Dict = None, op_type: str = OP_TYPE[3],
                     condition: Dict[Tuple[str, int or float or str or Tuple], str] = None,
                     limit: int = 100, offset: int = 0, field_quota: bool = True) -> str:
        """
        根据给定的值生成简单的sql，其中select语句最难生成，因此只能是给个参考，慎用本方法生成select语句
        :param field_quota: 是否需要在查询时，给字段名加引号
        :param offset: 分页查询时，从0开始的偏移量
        :param condition:键值对，键是元组，长度为两个元素，值是条件参数，例如：
        {("dass", 231): "="}，代码会转换为“dass” = 231 作为条件加入where语句
        :param limit:select 语句中防止查询过大，默认100
        :param kvs:修改，增加时，需要给定该参数，指示需要修改或新增行时的参数，例如
            {"id": 2, "file_execute": "file", "execute_time": "2022年11月1日21:24:58"}，代码会将之转换为如下：

            INSERT INTO `research`.`record_result` (`id`, `file_execute`, `execute_time`)
            VALUES (2, "file", "2022年11月1日21:24:58");

            UPDATE `research`.`record_result` SET `id` = 2, `file_execute` = "file",
            `execute_time` = "2022年11月1日21:24:58";

            SELECT `id`, `file_execute`, `execute_time` FROM `research`.`record_result`;

        :param op_type: 取值为["INSERT", "UPDATE", "DELETE", "SELECT"]，指明生成的sql类型
        :return:生成的sql
        """
        fields = []
        values = []
        condition_clause = "WHERE "
        if op_type == OP_TYPE[3] and (kvs is None or len(kvs) == 0):
            fields = "*"
        elif op_type == DELETE:
            fields = ""
        else:
            for kv in kvs.items():
                if field_quota:
                    fields.append("`" + str(kv[0]) + "`")
                else:
                    fields.append(str(kv[0]))
                t = type(kv[1])
                if t == int or t == float:
                    values.append(str(kv[1]))
                else:
                    values.append("\"" + str(kv[1]) + "\"")
        if condition is None or len(condition) == 0:
            condition_clause = ""
        else:
            count = 0
            for kv in condition.items():
                t = type(kv[0][1])
                if t == int or t == float:
                    condition_clause = condition_clause + str(kv[0][0]) + " " + str(kv[1]) + " " + str(kv[0][1])
                elif t == tuple:
                    tuple_str = str(kv[0][1]) if len(kv[0][1]) > 1 else str(kv[0][1]).replace(",", "")
                    condition_clause = condition_clause + str(kv[0][0]) + " " + str(kv[1]) + " " + tuple_str
                elif t == str:
                    condition_clause = condition_clause + \
                                       str(kv[0][0]) + " " + str(kv[1]) + " " + "\"" + str(kv[0][1]) + "\""
                if count < len(condition) - 1:
                    condition_clause = condition_clause + " AND "
                count = count + 1
        if op_type not in OP_TYPE:
            op_type = SELECT
        if op_type == INSERT:
            sql = "INSERT INTO `" + self.db_database + "`.`" + self.db_table + "` ({})" + " VALUES ({});"
            sql = sql.format(", ".join(fields), ", ".join(values))
        elif op_type == UPDATE:
            sql = "UPDATE `" + self.db_database + "`.`" + self.db_table + "` SET {} {};"
            modify = ""
            for i in range(len(fields)):
                modify = modify + fields[i] + " = " + values[i]
                if i < len(fields) - 1:
                    modify = modify + ", "
            sql = sql.format(modify, condition_clause)
        elif op_type == DELETE:
            sql = "DELETE FROM `" + self.db_database + "`.`" + self.db_table + "` {};"
            sql = sql.format(condition_clause)
        elif op_type == SELECT:
            sql = "SELECT" + " {} ".format(
                ", ".join(fields)) + "FROM `" + self.db_database + "`.`" + self.db_table + "` {} LIMIT {} OFFSET {};". \
                      format(condition_clause, str(limit), str(offset))
        return sql

    def create_db_conn(self):
        """
        链接数据库，不返回链接，全局使用一个连接conn
        :return:
        """
        connection = pymysql.connect(host=self.db_url,
                                     user=self.db_username,
                                     password=self.db_pass,
                                     db=self.db_database,
                                     port=self.port,
                                     charset="utf8"
                                     )
        self.conn = connection
        self.conn.autocommit(True)

    def query_table_field(self):
        """
        查询表中所有的字段名称
        :return:
        """
        sql = "select COLUMN_NAME from information_schema.COLUMNS where table_name = '{}';".format(self.db_table)
        if self.execute(sql):
            return [i[0] for i in self.cursor.fetchall()]
        else:
            return []

    def execute(self, sql: str) -> bool:
        """
        内部方法，执行sql
        也可以执行用户自定义的sql，比如利用建表时默认的四个默认列记录数据等
        :param show_sql: 是否在执行时，显示sql
        :param sql: 待执行的sql
        :return:
        """
        if self.show_sql:
            log(sql)
        try:
            self.cursor.execute(sql)
            return True
        except Exception as e:
            log("执行失败：{}".format(e))
            if self.ignore_error:
                write_file(local_path_generate("", "record_error.log"), mode="a+", string=sql + "\n")
            return False

    def select(self, condition: Dict = None, kvs: Dict or List = None, format: str = "one") -> List:
        """
        查询一个记录
        :param format: 查询的规模，"one"，代表查询一个记录， "all"代表查询所有
        :param kvs: 要查询的字段，可以接受字典，列表，其中字典的value并没有使用，只使用key
        :param condition:条件字典，形如{("a", "b") : "="} 即 where a = b
        :return:
        """
        if type(kvs) == list:
            t = {}
            for i in kvs:
                t[i] = ""
            kvs = t
        sql = self.generate_sql(condition=condition, op_type=SELECT, kvs=kvs)
        if self.execute(sql):
            return self.cursor.fetchone() if format == "one" else self.cursor.fetchall()
        else:
            return []

    def select_page(self, condition: Conditions = None, page: int = 100, page_no: int = 0) -> List[List]:
        """
        分页查找
        :param condition:条件
        :param page:页面大小
        :param page_no: 页面号
        :return:
        """
        res = []
        if condition is None:
            condition = Conditions()
        sql = self.generate_sql(kvs={"count(*) ": ""}, op_type=SELECT, condition=condition, field_quota=False)
        sum_page = None
        if self.execute(sql):
            sum_page = self.cursor.fetchone()[0]
            sum_page = int(sum_page / page) + 1
        else:
            sum_page = 0
        sql = self.generate_sql(op_type=SELECT, limit=page, offset=page_no * page, condition=condition)
        if self.execute(sql):
            return self.cursor.fetchall(), sum_page
        else:
            return [], 0

    def insert_one(self, kvs: Dict or List) -> bool:
        """
        插入一条记录
        :param kvs:需要插入的字段以及对应的值，当为list时，要求值与表所有字段对应
        :return:
        """
        if type(kvs) == list and len(kvs) != len(self.db_field):
            log("when input has only list, the len of list must equal with table fileds")
            return False
        elif type(kvs) == list and len(kvs) == len(self.db_field):
            t = {}
            for i in range(len(self.db_field)):
                t[self.db_field[i]] = kvs[i]
            kvs = t
        sql = self.generate_sql(kvs=kvs, op_type=INSERT)
        if self.execute(sql):
            return True
        else:
            return False

    def update(self, condition: Conditions, kvs: Dict or List) -> bool:
        """
        更新记录
        :param condition: 条件
        :param kvs: 需要插入的字段以及对应的值，当为list时，要求值与表所有字段对应
        :return:
        """
        if type(kvs) == list and len(kvs) != len(self.db_field):
            log("when input has only list, the len of list must equal with table fileds")
            return False
        elif type(kvs) == list and len(kvs) == len(self.db_field):
            t = {}
            for i in range(len(self.db_field)):
                t[self.db_field[i]] = kvs[i]
            kvs = t
        sql = self.generate_sql(kvs=kvs, op_type=UPDATE, condition=condition)
        if self.execute(sql):
            return True
        else:
            return False

    def delete(self, condition: Conditions) -> bool:
        """
        删除记录
        :param condition: 条件
        :return:
        """
        sql = self.generate_sql(op_type=DELETE, condition=condition)
        if self.execute(sql):
            return True
        else:
            return False
        return True

    def export(self, condition: Conditions, file_type: str = "csv", export_path: str = "",
               process: Callable[[List[str]], List] = None, field_name: List = None) -> bool:
        """
        导出文件
        :param field_name: 数据表中列的名称，默认为空
        :param process: 导出时对于列数据的处理，传入每行数据，输出改变后的每一行数据
        :param export_path: 导出文件的地址，默认为当前目录
        :param condition:条件
        :param file_type: 导出的类型，包括["csv", "xls"]
        :return:
        """
        if field_name is None:
            field_name = []
        res = list(self.select(condition, format="all"))
        if process is not None:
            for i in range(len(res)):
                try:
                    res[i] = process(res[i])
                except Exception as e:
                    log("处理数据程序错误：{}".format(e), print_file=sys.stderr)
        log("成功导出数据{}条".format(len(res)))
        res.insert(0, field_name)
        export_path = export_path if len(export_path) > 0 else \
            local_path_generate("", suffix=".csv" if file_type == "csv" else ".xls")
        try:
            if file_type == "csv":
                csv = CsvProcess()
                csv.write_csv(res, write_path=export_path)
            else:
                ExcelProcess().write_excel(res, path=export_path)
            return True
        except Exception as e:
            log("导出失败：{}".format(e))
            return False
        return True

    def __del__(self):
        """
        关闭连接
        :return:
        """
        if self.ssl.is_alive:
            self.ssl.stop()
        if self.conn is not None:
            self.conn.close()
        if self.cursor is not None:
            self.cursor.close()
        log("all file close !!!")


class ResearchRecord(object):
    """
    通过在程序中调用该对象方法，在数据库中记录参数，运行的文件， 运行的时间等信息
    也提供了基本的数据库操作的封装和导出，也可以执行自定义SQL
    建表语句可以通过类的静态方法获得：ResearchRecord.create_db_table()
    也可以自己建表，自己建表时至少继承如下列：
    ["id", "file_execute", "execute_time", "finish_time", "result", "args", "other"， "delete_flag"]
    """

    def __init__(self, **db_conf) -> None:
        """
        :param db_conf:详见readme文件
        """
        super().__init__()
        self.db_util = DB_util(**db_conf)
        self.conn = None
        self.cursor = None
        self.ssl = None
        if len(db_conf) <= 0:
            log("需要配置字典", print_file=sys.stderr)
            return None
        check_ssl = True if db_conf.get("ssl_ip") is not None and db_conf.get("ssl_admin") is not None and \
                            db_conf.get("ssl_pwd") is not None and db_conf.get("ssl_db_port") is not None \
                            and db_conf.get("ssl_port") is not None else False
        if check_ssl:
            self.ssl = SSHTunnelForwarder(
                ssh_address_or_host=(db_conf.get("ssl_ip"), db_conf.get("ssl_port")),
                ssh_username=db_conf.get("ssl_admin"),
                ssh_password=db_conf.get("ssl_pwd"),
                remote_bind_address=('localhost', db_conf.get("ssl_db_port"))
            )
            self.ssl.start()
        self.db_url = "127.0.0.1" if check_ssl else db_conf.get("db_url")
        self.db_username = db_conf.get("db_username")
        self.db_pass = db_conf.get("pass")
        self.port = self.ssl.local_bind_port if check_ssl else db_conf.get("port")
        self.db_database = db_conf.get("db_database") if db_conf.get("db_database") is not None else "research"
        self.db_table = db_conf.get("db_table") if db_conf.get("db_table") is not None else "record_result"
        self.db_type = "mysql"

        self.ignore_error = db_conf.get("ignore_error") if db_conf.get("ignore_error") is not None else True
        try:
            self.create_db_conn()
            self.cursor = self.conn.cursor()
        except Exception as e:
            log("链接数据库失败，请修改配置，云服务器请配置ssl：{}".format(e))

    @staticmethod
    def create_db_table():
        """
        返回建表建数据库语句
        :return:
        """
        log(CREATE_DB_TABLE)
        return CREATE_DB_TABLE

    def create_db_conn(self):
        """
        链接数据库，不返回链接，全局使用一个连接conn
        :return:
        """
        connection = pymysql.connect(host=self.db_url,
                                     user=self.db_username,
                                     password=self.db_pass,
                                     db=self.db_database,
                                     port=self.port,
                                     charset="utf8"
                                     )
        self.conn = connection
        self.conn.autocommit(True)

    def _execute(self, sql: str) -> bool:
        """
        内部方法，执行sql
        也可以执行用户自定义的sql，比如利用建表时默认的四个默认列记录数据等
        :param sql: 待执行的sql
        :return:
        """
        try:
            self.cursor.execute(sql)
            return True
        except Exception as e:
            log("执行失败：{}".format(e))
            if self.ignore_error:
                write_file(local_path_generate("", "record_error.log"), mode="a+", string=sql + "\n")
            return False

    def insert(self, file: str, exec_time: str, args: str = "") -> tuple:
        """
        插入，初始化记录，记录执行的文件，开始的时间
        :param args: 运行参数
        :param file: 执行的文件，使用__file__即可
        :param exec_time: 开始执行的时间
        :return:
        """
        exec_time = exec_time if len(exec_time) > 0 else get_timestamp()
        sql = "insert into `{}`.`{}`(`file_execute`, `excute_time`, `args`) " \
              "values ('{}', '{}','{}')".format(self.db_database, self.db_table,
                                                pymysql.converters.escape_string(file), exec_time,
                                                pymysql.converters.escape_string(args))
        if self._execute(sql):
            sql = "select   id   from  " + self.db_database + "." + self.db_table + \
                  " order   by   id   desc   limit   1"
            if self._execute(sql):
                return self.cursor.fetchone()[0]
            else:
                return -1,
        else:
            return -1,

    def update(self, id: int, finish_time: str = "", result: str = "", remark: str = "") -> bool:
        """
        执行结束之后，使用该方法更新
        :param remark: 备注
        :param args: 运行参数
        :param id: 要更新的记录id，可以从插入方法的返回值获得
        :param finish_time: 结束的时间
        :param result: 执行的结果
        :return:
        """
        finish_time = finish_time if len(finish_time) > 0 else get_timestamp()
        sql = "update `" + self.db_database + "`.`" + self.db_table + \
              "` set result='{}', finish_time='{}', other='{}' where id = {}". \
                  format(pymysql.converters.escape_string(result), finish_time,
                         pymysql.converters.escape_string(remark), str(id))
        if self._execute(sql):
            return True
        else:
            return False

    def select_all(self):
        """
        查询所有数据
        :return:
        """
        sql = "select count(*) from `" + self.db_database + "`.`" + self.db_table + "`"
        res = []
        if self._execute(sql):
            num = self.cursor.fetchone()[0]
            for i in range(int(num / 100) + 1):
                res.extend(self.select_page(page_no=i))
            return res
        else:
            return []

    def select_page(self, page: int = 100, page_no: int = 0, delete_flag: int = 0) -> List:
        """
        分页查找
        :param delete_flag: 删除标记
        :param page:页面大小
        :param page_no: 页面号
        :return:
        """
        res = []
        sql = "select count(*) from `" + self.db_database + "`.`" + self.db_table + "` WHERE `delete_flag` = " + \
              "{}".format(str(delete_flag))
        sum_page = None
        if self._execute(sql):
            sum_page = self.cursor.fetchone()[0]
            sum_page = int(sum_page / page) + 1
        else:
            sum_page = 0
        sql = "select * from `" + self.db_database + "`.`" + self.db_table + "` WHERE `delete_flag` = " + \
              "{}".format(str(delete_flag)) + " LIMIT {} OFFSET {}".format(str(page), str(page_no * page))
        if self._execute(sql):
            return self.cursor.fetchall(), sum_page
        else:
            return [], 0

    def export(self, id_range: tuple or List = [-100], file_type: str = "csv", export_path: str = "",
               process: Callable[[List[str]], List] = None) -> bool:
        """
        导出文件
        :param process: 导出时对于列数据的处理，传入每行数据，输出改变后的每一行数据
        :param export_path: 导出文件的地址，默认为当前目录
        :param id_range:id的范围，可以在select general中查询，当id_range中有负值存在时，只生效最小的负值，例如-110，-200，-200生效
        负值表示从倒数方向导出，i.e. -100表示导出最后100条。 tuple表示连续的id值，list表示单个id，tuple不支持负值
        i.e. : 给定tuple=(106, 224)，会查找id在[106, 224)的记录，所以如果需要导出106-224的记录，请输入(106, 225)
        :param file_type: 导出的类型，包括["csv", "xls"]
        :return:
        """
        id_list = []
        neg_id_min = 0
        id_list, neg_id_min = self.generate_id(id_range)
        res_list = []
        if neg_id_min < 0:
            sql = "select * from  " + self.db_database + "." + self.db_table + \
                  " order by id desc limit {}".format(str(abs(neg_id_min)))
            if self._execute(sql):
                temp = []
                for i in self.cursor.fetchall():
                    temp.append(list(i))
                res_list.extend(temp)
            else:
                res_list.extend([])

        s = ""
        for i in range(len(id_list)):
            if i == len(id_list) - 1:
                s = s + "'" + str(id_list[i]) + "'"
            else:
                s = s + "'" + str(id_list[i]) + "', "
        sql = "select * from  " + self.db_database + "." + self.db_table + \
              " where id in({})".format(s)
        if self._execute(sql):
            temp = []
            for i in self.cursor.fetchall():
                temp.append(list(i))
            res_list.extend(temp)
        else:
            res_list.extend([])
        if process is not None:
            for i in range(len(res_list)):
                try:
                    res_list[i] = process(res_list[i])
                except Exception as e:
                    log("处理数据程序错误：{}".format(e), print_file=sys.stderr)
        log("成功导出数据{}条".format(len(res_list)))
        res_list.insert(0, TABLE_TITLE)
        export_path = export_path if len(export_path) > 0 else \
            local_path_generate("", suffix=".csv" if file_type == "csv" else ".xls")
        try:
            if file_type == "csv":
                csv = CsvProcess()
                csv.write_csv(res_list, write_path=export_path)
            else:
                ExcelProcess().write_excel(res_list, path=export_path)
            return True
        except Exception as e:
            log("导出失败：{}".format(e))
            return False

    def generate_sql(self, kvs: Dict = None, op_type: str = OP_TYPE[3],
                     condition: Dict[Tuple[str, int or float or str or Tuple], str] = None,
                     limit: int = 100) -> str:
        """
        根据给定的值生成简单的sql，其中select语句最难生成，因此只能是给个参考，慎用本方法生成select语句
        :param condition:键值对，键是元组，长度为两个元素，值是条件参数，例如：
        {("dass", 231): "="}，代码会转换为“dass” = 231 作为条件加入where语句
        :param limit:select 语句中防止查询过大，默认100
        :param kvs:修改，增加时，需要给定该参数，指示需要修改或新增行时的参数，例如
            {"id": 2, "file_execute": "file", "execute_time": "2022年11月1日21:24:58"}，代码会将之转换为如下：

            INSERT INTO `research`.`record_result` (`id`, `file_execute`, `execute_time`)
            VALUES (2, "file", "2022年11月1日21:24:58");

            UPDATE `research`.`record_result` SET `id` = 2, `file_execute` = "file",
            `execute_time` = "2022年11月1日21:24:58";

            SELECT `id`, `file_execute`, `execute_time` FROM `research`.`record_result`;

        :param op_type: 取值为["INSERT", "UPDATE", "DELETE", "SELECT"]，指明生成的sql类型
        :return:生成的sql
        """
        fields = []
        values = []
        condition_clause = "WHERE "
        if op_type == OP_TYPE[3] and (kvs is None or len(kvs) == 0):
            fields = "*"
        elif op_type == DELETE:
            fields = ""
        else:
            for kv in kvs.items():
                fields.append("`" + str(kv[0]) + "`")
                t = type(kv[1])
                if t == int or t == float:
                    values.append(str(kv[1]))
                else:
                    values.append("\"" + str(kv[1]) + "\"")
        if condition is None or len(condition) == 0:
            condition_clause = ""
        else:
            count = 0
            for kv in condition.items():
                t = type(kv[0][1])
                if t == int or t == float:
                    condition_clause = condition_clause + str(kv[0][0]) + " " + str(kv[1]) + " " + str(kv[0][1])
                elif t == tuple:
                    tuple_str = str(kv[0][1]) if len(kv[0][1]) > 1 else str(kv[0][1]).replace(",", "")
                    condition_clause = condition_clause + str(kv[0][0]) + " " + str(kv[1]) + " " + tuple_str
                elif t == str:
                    condition_clause = condition_clause + \
                                       str(kv[0][0]) + " " + str(kv[1]) + " " + "\"" + str(kv[0][1]) + "\""
                if count < len(condition) - 1:
                    condition_clause = condition_clause + " AND "
                count = count + 1
        if op_type not in OP_TYPE:
            op_type = OP_TYPE[3]
        if op_type == OP_TYPE[0]:
            sql = "INSERT INTO `" + self.db_database + "`.`" + self.db_table + "` ({})" + " VALUES ({});"
            sql = sql.format(", ".join(fields), ", ".join(values))
        elif op_type == OP_TYPE[1]:
            sql = "UPDATE `" + self.db_database + "`.`" + self.db_table + "` SET {} {};"
            modify = ""
            for i in range(len(fields)):
                modify = modify + fields[i] + " = " + values[i]
                if i < len(fields) - 1:
                    modify = modify + ", "
            sql = sql.format(modify, condition_clause)
        elif op_type == OP_TYPE[2]:
            sql = "DELETE FROM `" + self.db_database + "`.`" + self.db_table + "` {};"
            sql = sql.format(condition_clause)
        elif op_type == OP_TYPE[3]:
            sql = "SELECT" + " {} ".format(
                ", ".join(fields)) + "FROM `" + self.db_database + "`.`" + self.db_table + "` {} LIMIT {};". \
                      format(condition_clause, str(limit))
        return sql

    def delete(self, ids: List or Tuple) -> bool:
        """
        对特定元素进行标记删除
        :param ids: id的范围，可以在select general中查询，当id_range中有负值存在时，只生效最小的负值，例如-110，-200，-200生效
        负值表示从倒数方向导出，i.e. -100表示删除最后100条。 tuple表示连续的id值，list表示单个id，tuple不支持负值
        i.e. : 给定tuple=(106, 224)，会查找id在[106, 224)的记录，所以如果需要删除106-224的记录，请输入(106, 225)
        :return:
        """
        id_list, neg_id_min = self.generate_id(id_range=ids)
        if neg_id_min < 0:
            sql = "select id from  " + self.db_database + "." + self.db_table + \
                  " order by id desc limit {}".format(str(abs(neg_id_min)))
            self._execute(sql=sql)
            res = self.cursor.fetchall()
            id_list.extend(list(i[0] for i in res))
        sql = self.generate_sql({"delete_flag": 1}, op_type=OP_TYPE[1], condition={("id", tuple(id_list)): "in"})
        if self._execute(sql):
            return True
        else:
            return False

    def generate_id(self, id_range: List or Tuple) -> (list, int):
        """
        id的范围，可以在select general中查询，当id_range中有负值存在时，只生效最小的负值，例如-110，-200，-200生效
        负值表示从倒数方向导出，i.e. -100表示生成最后100条的id。 tuple表示连续的id值，list表示单个id，tuple不支持负值
        i.e. : 给定tuple=(106, 224)，会查找id[106, 224)，所以如果需要生成106-224的记录，请输入(106, 225)
        :param id_range:
        :return:
        """
        id_list = []
        neg_id_min = 0
        if id_range is None or len(id_range) == 0:
            return id_list, neg_id_min
        if type(id_range) == list:
            for i in id_range:
                if i < 0 and i < neg_id_min:
                    neg_id_min = i
                elif i > 0:
                    id_list.append(i)
            return id_list, neg_id_min
        elif type(id_range) == tuple:
            if len(id_range) == 1:
                if id_range[0] < 0 and id_range[0] < neg_id_min:
                    neg_id_min = id_range[0]
                elif id_range[0] > 0:
                    sql = "select id from  " + self.db_database + "." + self.db_table + \
                          " order by id desc limit {}".format(str(abs(-1)))
                    if self._execute(sql):
                        last_id = self.cursor.fetchone()[0]
                        l = id_range[0] if id_range[0] <= last_id else last_id
                        r = last_id if id_range[0] <= last_id else id_range[0]
                        for i in range(l, r + 1):
                            id_list.append(i)
                    else:
                        id_list.append(id_range[0])
            elif len(id_range) >= 2:
                l = id_range[0] if id_range[0] <= id_range[1] else id_range[1]
                r = id_range[1] if id_range[0] <= id_range[1] else id_range[0]
                for i in range(l, r):
                    id_list.append(i)
            return id_list, neg_id_min
        else:
            log("仅支持tuple和list", print_file=sys.stderr)
            return id_list, neg_id_min

    def modify(self, data: Dict) -> bool:
        try:
            id = data["id"]
        except Exception as e:
            log("请提供id，{}".format(e))
        other = data["other"]
        sql = self.generate_sql({"other": other}, condition={("id", id): "="}, op_type=OP_TYPE[1])
        if self._execute(sql):
            return True
        else:
            return False

    def get_by_id(self, data: Dict) -> List:
        """
        根据id获取信息
        :param data:
        :return:
        """
        try:
            id = data["id"]
        except Exception as e:
            log("请提供id，{}".format(e))
        sql = self.generate_sql(condition={("id", id): "="}, op_type=SELECT)
        if self._execute(sql):
            return list(self.cursor.fetchone())
        else:
            return []

    def select_page_condition(self, page: int = 100, page_no: int = 0, delete_flag: int = 0,
                              conditions: Conditions = None) -> List:
        """
        分页查找
        :param conditions: 条件
        :param delete_flag: 删除标记
        :param page:页面大小
        :param page_no: 页面号
        :return:
        """
        conditions.add_condition("delete_flag", delete_flag, "=")
        return self.db_util.select_page(condition=conditions, page=page, page_no=page_no)

    def __del__(self):
        """
        关闭连接
        :return:
        """
        if self.ssl.is_alive:
            self.ssl.stop()
        if self.conn is not None:
            self.conn.close()
        if self.cursor is not None:
            self.cursor.close()
        log("all file close !!!")


if __name__ == "__main__":
    basic_config(logs_style=LOG_STYLE_PRINT)

