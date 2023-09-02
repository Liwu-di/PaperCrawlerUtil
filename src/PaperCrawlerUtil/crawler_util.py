import re
from urllib.request import urlretrieve

from bs4 import BeautifulSoup

from PaperCrawlerUtil.common_util import *


def get_opener(require_proxy, random_proxy, need_random_header, proxies):
    opener = urllib.request.build_opener()
    if require_proxy and need_random_header:
        ua = UserAgent()
        if random_proxy and two_one_choose():
            opener.addheaders = [('User-Agent', ua.random),
                                 ('proxy', "http://" + proxies),
                                 ('proxy', "https://" + proxies)]
        elif random_proxy and not two_one_choose():
            opener.addheaders = [('User-Agent', ua.random)]
        else:
            opener.addheaders = [('User-Agent', ua.random)]
    elif require_proxy:
        if random_proxy and two_one_choose():
            opener.addheaders = [('proxy', "http://" + proxies),
                                 ('proxy', "https://" + proxies)]
    elif need_random_header:
        ua = UserAgent()
        opener.addheaders = [('User-Agent', ua.random)]
    return opener


def retrieve_file(url: str, path: str = "", proxies: str = "",
                  require_proxy: bool = False, max_retry: int = 10,
                  sleep_time: float = 1.2, random_proxy: bool = True,
                  need_log: bool = True, reporthook: Callable[[], None] = None,
                  data: str = None, need_random_header: bool = True) -> bool:
    """
    retrieve file from provided url and save to path
    :param need_random_header: 是否需要使用随机header
    :param data: 使用url encode的参数
    :param reporthook: 用来在获取url链接信息之后调用的函数,例如函数def test(a: int, b: int, c: int) -> None,
    三个参数分别表示，当前下载第几块，每块的大小，文件的总大小
    :param need_log: 是否需要日志
    :param url: file url
    :param path: the save path
    :param proxies: proxy string, if this args not null, will always use this proxy if decide to use proxy
    :param require_proxy:decide whether use proxy
    :param max_retry: max times to retry if fail to retrieve
    :param sleep_time: thread sleep time which finish part function
    :param random_proxy: if this arg is true, whatever provide proxy,
    will random to use local address to access url
    :return:a bool value represent whether success to save file
    """
    success = False
    proxy_provide = False
    if len(path) == 0:
        path = local_path_generate("")
    if len(proxies) == 0:
        proxy_provide = False
    else:
        proxy_provide = True
    for i in range(max_retry):
        if need_log:
            log("第{}次准备抽取{}文件".format(str(i), url))
        try:
            if len(proxies) == 0 and require_proxy:
                proxies = get_proxy()
            if not proxy_provide and require_proxy:
                proxies = get_proxy()
            opener = get_opener(require_proxy, random_proxy, need_random_header, proxies)
            urllib.request.install_opener(opener)
            bar = None
            if reporthook:
                reporthook = reporthook
            else:
                bar = process_bar(final_prompt="文件下载完成", desc="文件下载进度：")
                reporthook = bar.process
            urlretrieve(url=url, filename=path, reporthook=reporthook, data=data)
            success = True
            time.sleep(sleep_time)
        except Exception as e:
            log("抽取:{},失败:{}".format(url, e), print_file=sys.stderr)
            time.sleep(sleep_time)
        if success:
            return success
            time.sleep(sleep_time)
    if not success:
        log("{}提取失败".format(url), print_file=sys.stderr)
        time.sleep(sleep_time)
        return success


def get_pdf_link_from_sci_hub_download_page_and_download(html: str, work_path: str, sleep_time: float = 1.2,
                                                         max_retry: int = 10,
                                                         require_proxy: bool = False,
                                                         proxies: bool = "", need_log: bool = True) -> bool:
    attr_list = get_attribute_of_html(html, {"href=": "in"}, ["button"])
    for paths in attr_list:
        paths = str(paths)
        try:
            path = paths.split("href=")[1].split("?download")[0]
        except Exception as e:
            log("链接{}截取错误:{}".format(paths, e), print_file=sys.stderr)
            continue
        time.sleep(sleep_time)
        for i in range(max_retry):
            path = path.replace("'", "").replace("\"", "").replace(",", "")
            if (not path.startswith("http:")) and (not path.startswith("https:")):
                if "sci" not in path or "hub" not in path:
                    path = "https://" + random.choice(['sci-hub.se', 'sci-hub.st', 'sci-hub.ru']) + (
                        path.replace("//", "", 1))
                else:
                    path = "https://" + (path.replace("//", "", 1))
            else:
                path = path
            success = retrieve_file(
                path,
                work_path, proxies=proxies, require_proxy=require_proxy, max_retry=1)
            if success:
                if need_log:
                    log("文件{}提取成功".format(work_path))
                return True
        if not success:
            log("抽取文件达到最大次数，停止获取{}".format(path), print_file=sys.stderr)
            return False
    return False


def get_pdf_url_by_doi(search: str, work_path: str, sleep_time: float = 1.2, max_retry: int = 10,
                       require_proxy: bool = False, random_proxy: bool = True,
                       proxies: bool = "", need_log: bool = True, is_doi: bool = True) -> bool:
    """
    save file from sci_hub by doi string provided
    :param is_doi: search字段是否是doi，还是名称
    :param need_log: 是否需要日志
    :param require_proxy:是否需要代理
    :param random_proxy:是否在使用代理时，随机使用本机地址
    :param proxies:提供代理，如果提供，则一直使用该代理，并且受random_proxy影响
    :param search: 搜索字段
    :param work_path: file path to save
    :param sleep_time: thread sleep time which finish part function
    :param max_retry: max times to retry if fail to retrieve
    :return:
    """
    domain_list = ['sci-hub.se/', 'sci-hub.st/', 'sci-hub.ru/']
    html = ''

    if is_doi:
        for i in range(max_retry):
            url = 'https://' + domain_list[random.randint(0, 2)]
            url = url + search
            html = random_proxy_header_access(url,
                                              max_retry=1, proxy=proxies,
                                              random_proxy=random_proxy,
                                              require_proxy=require_proxy)
            if len(html) == 0:
                log("爬取失败，字符串长度为0", print_file=sys.stderr)
                time.sleep(sleep_time)
                continue
            elif len(html) != 0 and len(get_attribute_of_html(html, {"href=": "in"}, ["button"])) == 0:
                log("爬取失败，无法从字符串中提取需要的元素", print_file=sys.stderr)
                time.sleep(sleep_time)
                continue
            else:
                if need_log:
                    log("从sichub获取目标文件链接成功，等待分析提取")
                break
        if len(html) == 0:
            log("获取html文件达到最大次数，停止获取doi:{}".format(search), print_file=sys.stderr)
            return
        return get_pdf_link_from_sci_hub_download_page_and_download(html=html, work_path=work_path,
                                                                    sleep_time=sleep_time,
                                                                    max_retry=max_retry, require_proxy=require_proxy,
                                                                    proxies="", need_log=need_log)
    else:
        for i in range(max_retry):
            url = 'https://' + domain_list[random.randint(0, 2)]
            html = random_proxy_header_access(method=POST, post_data={"request": search}, require_proxy=require_proxy,
                                              max_retry=max_retry, sleep_time=sleep_time, random_proxy=random_proxy,
                                              need_log=need_log, return_type="object", url=url)
            if html is not None and \
                    verify_rule(rule={400: LESS_THAN, 200: GREATER_AND_EQUAL}, origin=float(html.status_code)):
                if verify_rule(rule={0: MORE_THAN}, origin=len(html.url)) \
                        and verify_rule(rule={"未找到文章": NOT_IN, "article not found": NOT_IN}, origin=html.text):
                    if need_log:
                        log("重定向到网址：{}".format(html.url))
                    download_page = random_proxy_header_access(method=GET, require_proxy=require_proxy,
                                                               max_retry=max_retry, sleep_time=sleep_time,
                                                               random_proxy=random_proxy,
                                                               need_log=need_log, return_type="str", url=html.url)
                    res = get_pdf_link_from_sci_hub_download_page_and_download(html=download_page, work_path=work_path,
                                                                               sleep_time=sleep_time,
                                                                               max_retry=max_retry,
                                                                               require_proxy=require_proxy,
                                                                               proxies=proxies,
                                                                               need_log=need_log)
                    if res:
                        return res
                else:
                    log("未查询到对应文件名文件: {}".format(search), print_file=sys.stderr)
                    return False
            elif html is not None:
                log("访问失败，状态为：{}".format(str(html.status_code)), print_file=sys.stderr)
            else:
                log("访问出错，再次尝试", print_file=sys.stderr)
        log("抽取文件达到最大次数，停止获取文件:{}".format(search), print_file=sys.stderr)
        return False


def get_attribute_of_html(html: str, rule: dict = None, attr_list: list = None) -> list:
    """
    Use beautifulsoup4 to scan the html string get by urllib.get().
    And select all attribute in attr_list and then select satisfy all rules in rule
    in list.then return the list which contains all attribute
    :param html: html string
    :param rule: a dictionary that represent rules. the key is the match string and the value
    is the rule. The rule is only support "in" and "not in". example:{"href": "in"}
    :param attr_list: a list that contain attribute which you want. example:["a", "button"]
    :return: a list of attribute string
    """
    if attr_list is None:
        attr_list = ['a']
    if rule is None:
        rule = {'href': 'in'}
    res_list = []
    if len(html) == 0:
        return res_list
    bs = BeautifulSoup(html, 'html.parser')
    elements_list = []
    for k in attr_list:
        elements_list.extend(bs.find_all(k))
    for elements in elements_list:
        if verify_rule(rule, elements):
            res_list.append(str(elements))
    return list(set(res_list))


def get_pdf_form_arXiv(title: str, folder_name: str, sleep_time: float = 1.2,
                       max_retry: int = 10, require_proxy: bool = False,
                       random_proxy: bool = True, proxies: str = "", max_get: int = 3) -> None:
    """
    从arXiv获取论文，
    :param title:
    :param folder_name:
    :param sleep_time:
    :param max_retry:
    :param require_proxy:
    :param random_proxy:
    :param proxies:
    :param max_get: 当搜索结果有多个时，最多获取的数量
    :return:
    """
    html = random_proxy_header_access(url="https://arxiv.org/search/?query="
                                          + title.replace(" ", "+")
                                          + "&searchtype=all&source=header",
                                      proxy=proxies, require_proxy=require_proxy, max_retry=max_retry,
                                      sleep_time=sleep_time, random_proxy=random_proxy)
    attr_list = get_attribute_of_html(html, rule={"pdf": IN, "arxiv": IN, "href": IN})
    count = 0
    for k in attr_list:
        path = k.split("href=\"")[1].split("\"")[0]
        retrieve_file(path,
                      local_path_generate(folder_name=folder_name, file_name=title + str(count) + ".pdf"),
                      proxies=proxies, require_proxy=require_proxy,
                      max_retry=max_retry, sleep_time=sleep_time, random_proxy=random_proxy)
        count = count + 1
        if count >= max_get:
            break
    get_split()


def google_scholar_search_crawler(contain_all: List[str] = None, contain_complete_sentence: List[str] = None,
                                  least_contain_one: List[str] = None, not_contain: List[str] = None,
                                  q: str = "", need_log: bool = True, sleep_time: float = 15,
                                  need_retrieve_file: bool = False, start: int = 0, proxy: str = "",
                                  file_sava_directory: str = "") -> object or List:
    """
    爬取谷歌学术爬虫
    :param contain_all:高级搜索，包含列表中全部字符
    :param contain_complete_sentence: 高级搜索，必须包含完整字句
    :param least_contain_one: 高级搜索，至少包含列表中的某一个字符
    :param not_contain: 高级搜索，不包含列表中的所有字符串
    :param q: 普通搜索，输入查询内容，优先级高于以上四个高级搜索关键词
    :param need_log: 是否需要日志
    :param sleep_time: 睡眠时间，防止被封ip
    :param need_retrieve_file: 是否需要爬取PDF文件，如果有
    :param start: 开始索引，必须为10的整数倍或者0
    :param proxy: 可以爬取谷歌的代理ip：port
    :param file_sava_directory: 文件保存的目录，文件名自动爬取
    :return: 返回文件列表或者html对象，参考need_retrieve_file
    """
    if len(proxy) == 0:
        log("谷歌学术需要提供代理", print_file=sys.stderr)
        return None
    if contain_all is None and contain_complete_sentence is None and least_contain_one is None and not_contain is None \
            and len(q) == 0:
        log("查询内容q或者高级查找关键词不能全部为空", print_file=sys.stderr)
        return None
    base_url = "https://scholar.google"
    base_url = base_url + random.choice(DOMAIN_LIST)
    base_url = base_url + "/scholar?start=" + str(start) + "&hl=zh-CN&as_sdt=0%2C5&q="
    q_ = "+".join(contain_all) + "+" \
         + "OR+" + "+OR+".join(least_contain_one) + "+" \
         + ("\"" + "+".join(contain_complete_sentence) + "\"") + "+" \
         + "-" + "+-".join(not_contain)
    q = q.replace(" ", "+")
    q = q if len(q) != 0 else q_
    base_url = base_url + q + "&oq="
    html = random_proxy_header_access(url=base_url, require_proxy=True, proxy=proxy,
                                      random_proxy=False, need_log=need_log, return_type="object",
                                      sleep_time=sleep_time)
    if need_retrieve_file:
        file_list = []
        if type(html) == str:
            html = html
        else:
            html = html.content
        div_list = get_attribute_of_html(html=html, rule={"div class=\"gs_r gs_or gs_scl\"": IN, "data-cid": IN,
                                                          "data-did": IN, "data-aid": IN, "data-rp": IN,
                                                          "引用": IN, "<div id=\"gs_top\" onclick=\"\">": NOT_IN,
                                                          "<div id=\"gs_bdy\">": NOT_IN,
                                                          "<div id=\"gs_bdy_ccl\" role=\"main\">": NOT_IN,
                                                          "<div id=\"gs_res_ccl\">": NOT_IN,
                                                          "<div id=\"gs_res_ccl_mid\">": NOT_IN},
                                         attr_list=["div"])
        for div in div_list:
            name = get_attribute_of_html(html=div, rule={"class=\"gs_rt\"": IN}, attr_list=["h3"])
            if len(name) != 0:
                name = deleteSpecialCharFromHtmlElement(html=name[0], sep="")
                name = name + ".pdf"
                name = name.replace(":", "")
            else:
                continue
            link = get_attribute_of_html(html=div, rule={"[PDF]": IN})[0].split("href=\"")[1].split("\">")[0]
            if len(link) == 0:
                log("文件：{}没有PDF可下载".format(name))
                continue
            file_sava_path = local_path_generate(file_sava_directory, file_name=name)
            retrieve_file(url=link, path=file_sava_path, need_log=False, require_proxy=True, proxies=proxy)
            log("文件：{}保存成功到：{}".format(name, file_sava_path))
            file_list.append(file_sava_path)
        return file_list
    else:
        return html


class HTTPLinkExtractor:
    def __init__(self):
        self.links = set()

    def extract_links(self, text, strict_mode=False):
        if strict_mode:
            self._extract_links_strict(text)
        else:
            self._extract_links_lax(text)

    def _extract_links_lax(self, text):
        links = re.findall(r'https?://[^\s/$.?#].[^\s]*', text)
        self.links.update(links)

        domain_links = re.findall(r'(?<!https?://)www\.[^\s/$.?#].[^\s]*', text)
        self.links.update(domain_links)

    def _extract_links_strict(self, text):
        self._extract_links_lax(text)

    def get_unique_links(self):
        return list(self.links)


if __name__ == "__main__":
    input_text = input("请输入文本：")
    extractor = HTTPLinkExtractor()

    try:
        # 默认模式，尽可能多地识别链接
        extractor.extract_links(input_text)
        all_links = extractor.get_unique_links()

        print("尽可能多地识别的链接：")
        for link in all_links:
            print(link)

        # 严格模式，确保正确识别链接
        extractor.extract_links(input_text, strict_mode=True)
        strict_links = extractor.get_unique_links()

        print("\n确保正确识别的链接：")
        for link in strict_links:
            print(link)

    except Exception as e:
        print(f"处理时出现异常：{e}")

if __name__ == "__main__":
    basic_config(logs_style=LOG_STYLE_PRINT)
