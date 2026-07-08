"""生成 KeyGuard 硬件钱包 demo 的 records.csv 使用记录数据。

用途：运行 `python3 scripts/generate_records.py` 可重新生成
data/external/records.csv。数据为模拟数据，用于展示报告链路，不代表真实用户数据。
"""
import csv
import os
import random
from datetime import datetime


random.seed(42)

USER_PROFILES = {
    "1001": {"model": "KeyGuard Mini", "chains": "BTC, ETH", "risk_base": 1, "backup": True},
    "1002": {"model": "KeyGuard Pro", "chains": "ETH, Polygon, Arbitrum", "risk_base": 2, "backup": True},
    "1003": {"model": "KeyGuard Mini", "chains": "USDT-TRC20, ETH", "risk_base": 3, "backup": False},
    "1004": {"model": "KeyGuard Max", "chains": "BTC, ETH, SOL", "risk_base": 1, "backup": True},
    "1005": {"model": "KeyGuard Pro", "chains": "ETH, BTC, SOL", "risk_base": 2, "backup": True},
    "1006": {"model": "KeyGuard Pro", "chains": "ETH, BSC", "risk_base": 2, "backup": False},
    "1007": {"model": "KeyGuard Mini", "chains": "BTC", "risk_base": 1, "backup": True},
    "1008": {"model": "KeyGuard Max", "chains": "ETH, Arbitrum, Polygon", "risk_base": 3, "backup": True},
    "1009": {"model": "KeyGuard Pro", "chains": "SOL, ETH", "risk_base": 2, "backup": True},
    "1010": {"model": "KeyGuard Max", "chains": "BTC, ETH, TRX", "risk_base": 1, "backup": True},
}


def build_months() -> list[str]:
    """动态生成月份列表：从 2025-01 到脚本运行当月。"""
    start = datetime(2025, 1, 1)
    now = datetime.now()
    months: list[str] = []
    y, m = start.year, start.month
    while (y, m) <= (now.year, now.month):
        months.append(f"{y}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


MONTHS = build_months()


def gen_usage(profile: dict, month_idx: int) -> str:
    sign_count = random.randint(8, 35)
    receive_count = random.randint(2, 18)
    return "\n".join([
        f"设备型号:{profile['model']}",
        f"常用链:{profile['chains']}",
        f"签名次数:{sign_count}次/月",
        f"收款地址核对:{receive_count}次/月",
    ])


def gen_security(profile: dict, month_idx: int) -> str:
    firmware_status = "已是最新版" if month_idx % 5 else "建议升级"
    backup_status = "已验证" if profile["backup"] else "未验证"
    passphrase_status = "已开启" if profile["risk_base"] <= 2 else "未开启"
    return "\n".join([
        f"固件状态:{firmware_status}",
        f"助记词备份:{backup_status}",
        f"Passphrase:{passphrase_status}",
        f"高风险授权:{max(0, profile['risk_base'] - 1 + random.randint(0, 1))}个",
    ])


def gen_transaction(profile: dict, month_idx: int) -> str:
    failed_txs = random.randint(0, profile["risk_base"])
    pending_txs = random.randint(0, 2)
    return "\n".join([
        f"失败交易:{failed_txs}笔",
        f"长时间未确认交易:{pending_txs}笔",
        f"小额测试:{random.randint(1, 6)}次",
        f"授权复核:{random.randint(0, 4)}次",
    ])


def gen_comparison(profile: dict) -> str:
    templates = [
        "风险操作低于{pct}%同类用户",
        "备份完整度高于{pct}%同类用户",
        "授权复核频率处于同类前{rank}%",
    ]
    template = random.choice(templates)
    if "{pct}" in template:
        return template.format(pct=random.randint(55, 85))
    return template.format(rank=random.randint(10, 35))


def main():
    output_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "external", "records.csv"
    )
    output_path = os.path.abspath(output_path)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["用户ID", "使用概况", "安全状态", "交易状态", "风险对比", "时间"])

        for uid, profile in USER_PROFILES.items():
            for m_idx, month in enumerate(MONTHS, start=1):
                writer.writerow([
                    uid,
                    gen_usage(profile, m_idx),
                    gen_security(profile, m_idx),
                    gen_transaction(profile, m_idx),
                    gen_comparison(profile),
                    month,
                ])

    print(f"已生成 {len(USER_PROFILES)} 个用户 × {len(MONTHS)} 个月 = {len(USER_PROFILES) * len(MONTHS)} 条记录")
    print(f"输出：{output_path}")


if __name__ == "__main__":
    main()
