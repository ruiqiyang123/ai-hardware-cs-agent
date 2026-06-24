"""生成更真实的 records.csv 使用记录数据。

用途：运行 `python scripts/generate_records.py` 可重新生成 data/external/records.csv。
每次生成的数据会有随机波动（模拟真实使用），但用户画像和耗材趋势保持一致。

改造点：原 records.csv 是写死的手工数据，无法调整。
现在做成脚本化生成，便于：
1. 扩展用户数 / 月份范围
2. 在评测时构造特定场景的数据
3. 面试时能讲清楚数据是怎么来的
"""
import csv
import random
import os
from datetime import datetime

random.seed(42)  # 固定种子，保证可复现

# 用户画像：每个用户的家庭/房屋特征是固定的（符合真实情况）
USER_PROFILES = {
    "1001": {"house": "65㎡公寓 | 单身 | 木地板", "base_coverage": 85},
    "1002": {"house": "70㎡公寓 | 情侣 | 瓷砖", "base_coverage": 88},
    "1003": {"house": "90㎡ | 1狗 | 短毛地毯", "base_coverage": 80, "pet": True},
    "1004": {"house": "85㎡ | 2猫 | 混合地面", "base_coverage": 82, "pet": True},
    "1005": {"house": "120㎡ | 老人 | 防滑砖", "base_coverage": 75, "elder": True},
    "1006": {"house": "150㎡别墅 | 儿童 | 多层", "base_coverage": 78},
    "1007": {"house": "55㎡一居 | 独居 | 复合地板", "base_coverage": 90},
    "1008": {"house": "100㎡三居 | 三口之家 | 大理石", "base_coverage": 86},
    "1009": {"house": "80㎡两居 | 养宠 | 仿实木", "base_coverage": 84, "pet": True},
    "1010": {"house": "130㎡四居 | 三代同堂 | 通体砖", "base_coverage": 80},
}

MONTHS = [f"2025-{m:02d}" for m in range(1, 13)]


def gen_feature(profile: dict, month_idx: int) -> str:
    """生成特征字段：覆盖率在基准值附近波动。"""
    base = profile["base_coverage"]
    coverage = base + random.randint(-3, 3)
    daily_area = int(profile["house"].split("㎡")[0]) * random.uniform(0.4, 0.6)

    parts = [f"覆盖率:{coverage}%", f"日均清扫:{daily_area:.0f}㎡"]
    if profile.get("pet"):
        parts.append(f"毛发清理:{random.randint(80, 95)}%")
    if profile.get("elder"):
        parts.append(f"手动操作占比:{random.randint(85, 95)}%")
    parts.append(f"避障成功率:{random.randint(85, 95)}%")
    return "\n".join(parts)


def gen_efficiency(profile: dict, month_idx: int) -> str:
    """生成效率字段。"""
    parts = [
        f"清扫效率:{random.uniform(0.7, 0.95):.0%}",
        f"定时任务使用:{random.randint(10, 30)}次/月",
    ]
    return "\n".join(parts)


def gen_consumables(month_idx: int) -> str:
    """生成耗材字段：随月份推进，耗材逐渐消耗。"""
    # 主刷寿命随时间递减
    brush_life = max(10, 365 - month_idx * 25 + random.randint(-10, 10))
    hepa = max(10, 100 - month_idx * 7 - random.randint(0, 5))
    parts = [
        f"主刷寿命:剩余{brush_life}天",
        f"HEPA滤网:剩余{hepa}%",
        f"尘盒清理:每{random.choice([2, 3, 5])}天",
    ]
    return "\n".join(parts)


def gen_comparison(profile: dict) -> str:
    """生成对比字段。"""
    templates = [
        "优于{pct}%同面积用户",
        "清洁频率高于同类{pct}%",
        "清洁效率处于同类前{rank}%",
    ]
    t = random.choice(templates)
    if "{pct}" in t:
        return t.format(pct=random.randint(55, 80))
    return t.format(rank=random.randint(10, 30))


def main():
    output_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "external", "records.csv"
    )
    output_path = os.path.abspath(output_path)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["用户ID", "特征", "清洁效率", "耗材", "对比", "时间"])

        for uid, profile in USER_PROFILES.items():
            for m_idx, month in enumerate(MONTHS, start=1):
                writer.writerow([
                    uid,
                    gen_feature(profile, m_idx),
                    gen_efficiency(profile, m_idx),
                    gen_consumables(m_idx),
                    gen_comparison(profile),
                    month,
                ])

    print(f"✅ 已生成 {len(USER_PROFILES)} 个用户 × {len(MONTHS)} 个月 = {len(USER_PROFILES)*len(MONTHS)} 条记录")
    print(f"   输出：{output_path}")


if __name__ == "__main__":
    main()
