import os
import csv
from datetime import datetime
from typing import Optional

import requests
from utils.logger_handler import logger
from langchain_core.tools import tool

from rag.rag_service import RagSummarizeService
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path
from utils.session_context import current_user_id, current_location

rag = RagSummarizeService()

# 会话级用户上下文：替代原 random.choice(user_ids)
# 在 Streamlit 前端通过 session_state 设置当前登录用户，见 app.py 侧边栏

external_data = {}


@tool(description="从向量存储中检索参考资料，返回包含答案与引用来源的结构化内容")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)


@tool(description="获取指定城市的实时天气信息（气温、湿度、降雨概率），用于判断扫地机器人是否适合拖地。返回纯字符串")
def get_weather(city: str) -> str:
    """通过 Open-Meteo 免费 API 获取真实天气数据，无需 API Key。

    改造点：原工具返回写死的「晴天26度」mock 数据，无法反映真实环境。
    现接入 Open-Meteo，让 Agent 能基于真实湿度/降雨概率给出拖地建议。
    """
    try:
        # 步骤1：城市名 → 经纬度（geocoding）
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(geo_url, params={"name": city, "count": 1, "language": "zh"}, timeout=5)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            return f"未找到城市：{city}，请确认城市名称"

        loc = geo_data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]

        # 步骤2：经纬度 → 实时天气
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_resp = requests.get(weather_url, params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m",
            "timezone": "auto",
        }, timeout=5)
        weather_resp.raise_for_status()
        current = weather_resp.json().get("current", {})

        temp = current.get("temperature_2m", "未知")
        humidity = current.get("relative_humidity_2m", "未知")
        rain_prob = current.get("precipitation_probability", "未知")
        wind = current.get("wind_speed_10m", "未知")

        return (f"城市{city}实时天气：气温{temp}°C，空气湿度{humidity}%，"
                f"未来1小时降雨概率{rain_prob}%，风速{wind}km/h")
    except requests.exceptions.Timeout:
        logger.warning(f"[get_weather]查询城市{city}天气超时")
        return f"查询{city}天气超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        logger.error(f"[get_weather]查询城市{city}天气失败：{e}")
        return f"查询{city}天气失败：{str(e)}"
    except Exception as e:
        logger.error(f"[get_weather]未知错误：{e}", exc_info=True)
        return f"获取{city}天气时发生未知错误"


@tool(description="获取当前用户的所在城市，返回纯字符串城市名。优先使用前端设置的会话位置，兜底用 IP 定位")
def get_user_location() -> str:
    """改造点：原工具 random.choice(['深圳','合肥','杭州'])。

    现在优先从会话上下文取（前端可手动指定位置），
    若未设置则用 ip-api.com 做 IP 粗略定位作为兜底。
    """
    # 优先用会话级位置（前端侧边栏可设置）
    loc = current_location()
    if loc:
        return loc

    # 兜底：IP 定位
    try:
        resp = requests.get("http://ip-api.com/json/", params={"lang": "zh"}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        city = data.get("city") or data.get("regionName") or "未知"
        logger.info(f"[get_user_location]IP定位城市：{city}")
        return city
    except Exception as e:
        logger.warning(f"[get_user_location]IP定位失败：{e}，使用默认城市")
        return "深圳"  # 最后兜底


@tool(description="获取当前登录用户的ID，返回纯字符串。ID 来自前端会话上下文")
def get_user_id() -> str:
    """改造点：原工具 random.choice(user_ids)。

    真实产品里用户ID是会话绑定的（登录后固定），
    现从 session_context 取，前端侧边栏可切换用户。
    """
    uid = current_user_id()
    logger.info(f"[get_user_id]当前会话用户ID：{uid}")
    return uid


@tool(description="获取系统当前月份，格式 YYYY-MM（如 2025-06），返回纯字符串")
def get_current_month() -> str:
    """改造点：原工具 random.choice(month_arr)。

    真实场景应返回系统当前月份，而非随机月份。
    """
    now = datetime.now()
    month_str = now.strftime("%Y-%m")
    logger.info(f"[get_current_month]系统当前月份：{month_str}")
    return month_str


def generate_external_data():
    """加载外部使用记录数据。

    数据结构：
    {
        "user_id": {
            "2025-01": {"特征": ..., "效率": ..., "耗材": ..., "对比": ...},
            ...
        },
        ...
    }
    """
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])

        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f"外部数据文件{external_data_path}不存在")

        # 用 csv 模块解析，正确处理字段内的换行和引号
        with open(external_data_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            for row in reader:
                if len(row) < 6:
                    logger.warning(f"[fetch_external_data]跳过不完整行：{row}")
                    continue

                user_id: str = row[0]
                feature: str = row[1]
                efficiency: str = row[2]
                consumables: str = row[3]
                comparison: str = row[4]
                time: str = row[5]

                if user_id not in external_data:
                    external_data[user_id] = {}

                external_data[user_id][time] = {
                    "特征": feature,
                    "效率": efficiency,
                    "耗材": consumables,
                    "对比": comparison,
                }


@tool(description="从外部系统中获取指定用户在指定月份的使用记录，以纯字符串形式返回。未检索到返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()

    try:
        return str(external_data[user_id][month])
    except KeyError:
        logger.warning(f"[fetch_external_data]未能检索到用户：{user_id}在{month}的使用记录数据")
        return ""


@tool(description="无入参，调用后触发中间件自动为报告生成场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report已调用"
