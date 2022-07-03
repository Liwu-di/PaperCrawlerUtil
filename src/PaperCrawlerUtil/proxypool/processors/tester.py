import asyncio
import aiohttp
from loguru import logger
from proxypool.schemas import Proxy
from proxypool.storages.redis import RedisClient
from proxypool.setting import TEST_TIMEOUT, TEST_BATCH, TEST_URL, TEST_VALID_STATUS, TEST_ANONYMOUS, NEED_LOG_TESTER
from aiohttp import ClientProxyConnectionError, ServerDisconnectedError, ClientOSError, ClientHttpProxyError
from asyncio import TimeoutError


EXCEPTIONS = (
    ClientProxyConnectionError,
    ConnectionRefusedError,
    TimeoutError,
    ServerDisconnectedError,
    ClientOSError,
    ClientHttpProxyError,
    AssertionError
)


class Tester(object):
    """
    tester for testing proxies in queue
    """
    
    def __init__(self, need_log=True):
        """
        init redis
        """
        self.redis = RedisClient()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = asyncio.get_event_loop()
        self.need_log = need_log
    
    async def test(self, proxy: Proxy):
        """
        test single proxy
        :param proxy: Proxy object
        :return:
        """
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            try:
                if self.need_log:
                    logger.debug(f'testing {proxy.string()}')
                # if TEST_ANONYMOUS is True, make sure that
                # the proxy has the effect of hiding the real IP
                if TEST_ANONYMOUS:
                    url = 'https://httpbin.org/ip'
                    async with session.get(url, timeout=TEST_TIMEOUT) as response:
                        resp_json = await response.json()
                        origin_ip = resp_json['origin']
                    async with session.get(url, proxy=f'http://{proxy.string()}', timeout=TEST_TIMEOUT) as response:
                        resp_json = await response.json()
                        anonymous_ip = resp_json['origin']
                    assert origin_ip != anonymous_ip
                    assert proxy.host == anonymous_ip
                async with session.get(TEST_URL, proxy=f'http://{proxy.string()}', timeout=TEST_TIMEOUT,
                                       allow_redirects=False) as response:
                    if response.status in TEST_VALID_STATUS:
                        self.redis.max(proxy)
                        if self.need_log:
                            logger.debug(f'proxy {proxy.string()} is valid, set max score')
                    else:
                        self.redis.decrease(proxy)
                        if self.need_log:
                            logger.debug(f'proxy {proxy.string()} is invalid, decrease score')
            except EXCEPTIONS:
                self.redis.decrease(proxy)
                if self.need_log:
                    logger.debug(f'proxy {proxy.string()} is invalid, decrease score')
    
    @logger.catch
    def run(self):
        """
        test main method
        :return:
        """
        # event loop of aiohttp
        logger.info('stating tester...')
        count = self.redis.count()
        if self.need_log:
            logger.debug(f'{count} proxies to test')
        cursor = 0
        while True:
            if self.need_log:
                logger.debug(f'testing proxies use cursor {cursor}, count {TEST_BATCH}')
            cursor, proxies = self.redis.batch(cursor, count=TEST_BATCH)
            if proxies:
                tasks = [self.test(proxy) for proxy in proxies]
                self.loop.run_until_complete(asyncio.wait(tasks))
            if not cursor:
                break


def run_tester():
    host = '96.113.165.182'
    port = '3128'
    tasks = [tester.test(Proxy(host=host, port=port))]
    tester.loop.run_until_complete(asyncio.wait(tasks))


if __name__ == '__main__':
    tester = Tester()
    tester.run()
    # run_tester()
