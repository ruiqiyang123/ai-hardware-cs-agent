import os
from datetime import datetime

import requests
from utils.logger_handler import logger
from langchain_core.tools import tool

from rag.rag_service import RagSummarizeService
from utils.config_handler import agent_conf
from utils.path_tool import get_abs_path
from utils.session_context import current_user_id, current_location
from agent.services.weather_service import fetch_weather
from agent.services.usage_records import find_usage_record, load_usage_records

rag = RagSummarizeService()

# 会话级用户上下文：替代原 random.choice(user_ids)
# 在 Streamlit 前端通过 session_state 设置当前登录用户，见 app.py 侧边栏

# 模块级缓存：避免每次调用 fetch_external_data 都重读 CSV。
# 纯解析逻辑已抽到 agent.services.usage_records，这里只保留缓存 + 委托。
external_data = {}


def configure_rag_model(model):
    """按会话重置 RAG 总结服务使用的 chat 模型。

    Web 前端切换 provider / API Key 后调用本函数，让 rag_summarize 工具与
    ReactAgent 共用同一会话模型，避免「主对话用 MiMo、RAG 总结却走 DashScope
    且无 key 报错」的割裂。
    """
    global rag
    rag = RagSummarizeService(model=model)


@tool(description="从向量存储中检索参考资料，返回包含答案与引用来源的结构化内容")
def rag_summarize(query: str) -> str:
    return rag.rag_summarize(query)


@tool(description="获取指定城市的实时天气信息（气温、湿度、降水量、风速），用于判断扫地机器人是否适合拖地。返回纯字符串")
def get_weather(city: str) -> str:
    """通过 Open-Meteo 免费 API 获取真实天气数据，无需 API Key。

    改造点：原工具返回写死的「晴天26度」mock 数据，无法反映真实环境。
    现接入 Open-Meteo，让 Agent 能基于真实湿度/降水量给出拖地建议。
    实际 HTTP 调用逻辑委托给 agent.services.weather_service.fetch_weather，便于单测。
    """
    return fetch_weather(city)


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

    # 兜底：IP 定位（带重试，覆盖瞬时网络抖动）
    try:
        for attempt in range(3):
            try:
                resp = requests.get("http://ip-api.com/json/", params={"lang": "zh"}, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                city = data.get("city") or data.get("regionName") or "未知"
                logger.info(f"[get_user_location]IP定位城市：{city}")
                return city
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                if attempt < 2:
                    logger.info(f"[get_user_location]IP定位第{attempt + 1}次超时，重试中...")
                    continue
                raise
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
    """加载外部使用记录数据到模块级缓存（仅首次加载）。

    纯解析逻辑委托给 agent.services.usage_records.load_usage_records。
    """
    global external_data
    if not external_data:
        external_data_path = get_abs_path(agent_conf["external_data_path"])
        external_data = load_usage_records(external_data_path)


@tool(description="从外部系统中获取指定用户在指定月份的使用记录，以纯字符串形式返回。未检索到返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    generate_external_data()
    return find_usage_record(external_data, user_id, month, fallback_to_latest=True)


@tool(description="无入参，调用后触发中间件自动为报告生成场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report已调用"
