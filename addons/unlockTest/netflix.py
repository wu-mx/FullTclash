import asyncio
import aiohttp
from aiohttp import ClientConnectorError
from loguru import logger
from utils.collector import config

# collector section
netflix_url1 = config.config.get('netflixurl', "https://www.netflix.com/title/80113701")  # 非自制
netflix_url2 = "https://www.netflix.com/title/70242311"  # 自制


async def fetch_netflix_new(Collector, session: aiohttp.ClientSession, flag=1, proxy=None, reconnection=30):
    """
    新版Netflix检测
    :param flag
    :param Collector: 采集器
    :param session:
    :param proxy:
    :param reconnection: 重连次数
    :return:
    """
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8," +
                  "application/signed-exchange;v=b3;q=0.9",
        "accept-language": "zh-CN,zh;q=0.9",
        "sec-ch-ua": r"\"Not_A Brand\";v=\"99\", \"Google Chrome\";v=\"109\", \"Chromium\";v=\"109\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": r"\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/102.0.5005.63 Safari/537.36'
    }
    try:
        if flag == 1:
            async with session.get(netflix_url1, proxy=proxy, timeout=5, headers=headers) as res:
                if res.status == 200:  # 解锁非自制
                    text = await res.text()
                    try:
                        locate = text.find("preferredLocale")  # 定位到关键标签
                        if locate > 0:
                            region = text[locate + 29:locate + 31]
                            Collector.info['netflix_new'] = f"解锁({region})"
                        else:
                            region = "未知"
                            Collector.info['netflix_new'] = f"解锁({region})"
                    except Exception as e:
                        logger.error(e)
                        Collector.info['netflix_new'] = "N/A"
                elif res.status == 403:
                    if reconnection == 0:
                        logger.info("不支持非自制剧，正在检测自制剧...")
                        await fetch_netflix_new(Collector, session, flag=flag + 1, proxy=proxy, reconnection=5)
                        return
                    await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
                else:
                    logger.info("不支持非自制剧，正在检测自制剧...")
                    await fetch_netflix_new(Collector, session, flag=flag + 1, proxy=proxy, reconnection=reconnection)
        elif flag == 2:
            async with session.get(netflix_url2, proxy=proxy, timeout=5) as res:
                if res.status == 200:  # 解锁自制
                    Collector.info['netflix_new'] = "自制"
                elif res.status == 403:
                    if reconnection == 0:
                        Collector.info['netflix_new'] = "失败"
                        return
                    await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
                else:
                    Collector.info['netflix_new'] = "失败"
        else:
            return
    except ClientConnectorError as c:
        logger.warning("Netflix请求发生错误:" + str(c))
        if reconnection != 0 and reconnection > 27:
            await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['netflix_new'] = "连接错误"
    except asyncio.exceptions.TimeoutError:
        logger.warning("Netflix请求超时，正在重新发送请求......")
        if reconnection > 27:
            await fetch_netflix_new(Collector, session, flag=flag, proxy=proxy, reconnection=reconnection - 1)
        else:
            Collector.info['netflix_new'] = "超时"


def task(Collector, session, proxy):
    return asyncio.create_task(fetch_netflix_new(Collector, session, proxy=proxy))


# cleaner section
def get_netflix_info_new(ReCleaner):
    """
    获得hbo解锁信息
    :param ReCleaner:
    :return: str: 解锁信息: [解锁(地区代码)、失败、N/A]
    """
    try:
        if 'netflix_new' not in ReCleaner.data:
            logger.warning("采集器内无数据")
            return "N/A"
        else:
            logger.info("netflix解锁：" + str(ReCleaner.data.get('netflix_new', "N/A")))
            return ReCleaner.data.get('netflix_new', "N/A")
    except Exception as e:
        logger.error(e)
        return "N/A"


SCRIPT = {
    "MYNAME": "Netflix",
    "TASK": task,
    "GET": get_netflix_info_new
}
