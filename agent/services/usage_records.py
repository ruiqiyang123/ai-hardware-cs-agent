"""硬件钱包用户使用记录加载服务。

从 agent_tools.py 抽出来的原因：
- CSV 解析是纯逻辑，独立成 load_usage_records(path) 后可传任意临时路径做单测；
- agent_tools 的 fetch_external_data 只保留「模块级缓存 + 委托」，职责更单一。

数据结构：
    {
        "1001": {
            "2025-06": {"特征": "使用概况", "效率": "安全状态", "耗材": "交易状态", "对比": "风险对比"},
            ...
        },
        ...
    }
"""
import csv
import os

from utils.logger_handler import logger


def load_usage_records(path: str) -> dict:
    """从 CSV 文件加载全部用户使用记录，返回 {user_id: {month: {...}}}。

    用 csv 模块解析，正确处理字段内的换行和引号（records.csv 的特征/效率
    字段含多行文本）。跳过不完整行并记日志。
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"外部数据文件{path}不存在")

    records: dict = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # 跳过表头
        for row in reader:
            if len(row) < 6:
                logger.warning(f"[load_usage_records]跳过不完整行：{row}")
                continue

            user_id, feature, efficiency, consumables, comparison, time = row[:6]
            records.setdefault(user_id, {})[time] = {
                "特征": feature,
                "效率": efficiency,
                "耗材": consumables,
                "对比": comparison,
            }
    return records


def find_usage_record(
    records: dict,
    user_id: str,
    month: str,
    fallback_to_latest: bool = False,
) -> str:
    """从已加载记录中获取指定用户月份数据。

    当 demo 数据没有覆盖系统当前月份时，可回退到该用户最近可用月份，并在
    返回内容中附加数据说明，避免 Agent 在报告场景拿到空字符串后继续编造。
    """
    user_records = records.get(user_id, {})
    record = user_records.get(month)
    if record is not None:
        return str(record)

    logger.warning(f"[find_usage_record]未能检索到用户：{user_id}在{month}的使用记录数据")
    if not fallback_to_latest or not user_records:
        return ""

    latest_month = sorted(user_records.keys())[-1]
    latest_record = user_records[latest_month]
    return (
        f"{latest_record}\n\n"
        f"数据说明：未找到 {month} 的模拟使用记录，"
        f"以下使用最近可用月份 {latest_month} 的记录生成参考报告。"
    )


def fetch_usage_record(path: str, user_id: str, month: str) -> str:
    """获取指定用户在指定月份的硬件钱包使用记录，返回字符串；未检索到返回空字符串。"""
    records = load_usage_records(path)
    return find_usage_record(records, user_id, month)
