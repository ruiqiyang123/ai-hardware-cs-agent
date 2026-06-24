"""用户使用记录加载服务。

从 agent_tools.py 抽出来的原因：
- CSV 解析是纯逻辑，独立成 load_usage_records(path) 后可传任意临时路径做单测；
- agent_tools 的 fetch_external_data 只保留「模块级缓存 + 委托」，职责更单一。

数据结构：
    {
        "1001": {
            "2025-06": {"特征": ..., "效率": ..., "耗材": ..., "对比": ...},
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


def fetch_usage_record(path: str, user_id: str, month: str) -> str:
    """获取指定用户在指定月份的使用记录，返回字符串；未检索到返回空字符串。"""
    records = load_usage_records(path)
    record = records.get(user_id, {}).get(month)
    if record is None:
        logger.warning(f"[fetch_usage_record]未能检索到用户：{user_id}在{month}的使用记录数据")
        return ""
    return str(record)
