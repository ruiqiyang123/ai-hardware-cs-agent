"""区块链网络状态服务：返回指定链的模拟网络状态数据。

用途：为硬件钱包客服场景提供链状态查询能力。
返回网络拥堵程度、手续费区间、预计确认时间和客服建议。

数据为模拟数据，用于 Demo 演示。
"""

from utils.logger_handler import logger


# 模拟各链网络状态数据
_CHAIN_STATUS_DATA = {
    "BTC": {
        "network": "Bitcoin",
        "congestion": "中等",
        "fee_range": "15-30 sat/vB",
        "confirm_time": "10-30 分钟",
        "mempool_size": "~45,000 笔待确认",
        "advice": "当前网络拥堵程度中等，普通转账建议设置 20 sat/vB 手续费，紧急转账可设置 30 sat/vB。如非紧急，建议等待网络拥堵缓解后再操作。"
    },
    "ETH": {
        "network": "Ethereum",
        "congestion": "较高",
        "fee_range": "25-50 Gwei",
        "confirm_time": "1-3 分钟",
        "mempool_size": "~120,000 笔待确认",
        "advice": "当前以太坊网络 Gas 费较高，建议使用 EIP-1559 设置合理的 Max Fee 和 Priority Fee。非紧急交易可等待 Gas 降至 20 Gwei 以下。DeFi 操作建议在低峰时段进行。"
    },
    "SOL": {
        "network": "Solana",
        "congestion": "低",
        "fee_range": "0.000005-0.00001 SOL",
        "confirm_time": "~400 毫秒",
        "mempool_size": "无传统内存池",
        "advice": "Solana 网络当前状态良好，交易确认速度快、费用低。适合日常转账和 DeFi 操作。如遇到交易失败，可能是网络抖动，重试即可。"
    },
    "BSC": {
        "network": "BNB Smart Chain",
        "congestion": "低",
        "fee_range": "1-3 Gwei",
        "confirm_time": "~3 秒",
        "mempool_size": "~8,000 笔待确认",
        "advice": "BSC 网络当前运行正常，手续费低廉。适合日常交易和 DeFi 操作。注意区分 BSC 和 BEP2 网络，发送前确认目标网络正确。"
    },
    "TRX": {
        "network": "TRON",
        "congestion": "低",
        "fee_range": "~13 TRX (带宽) / 0 TRX (质押)",
        "confirm_time": "~3 秒",
        "mempool_size": "极低",
        "advice": "TRON 网络状态良好，手续费低。如果已质押足够的 TRX 获取带宽和能量，可以实现零手续费交易。USDT-TRC20 转账建议确认有足够的带宽。"
    },
    "ARB": {
        "network": "Arbitrum One",
        "congestion": "低",
        "fee_range": "0.1-0.5 Gwei",
        "confirm_time": "~1 秒",
        "mempool_size": "极低",
        "advice": "Arbitrum L2 网络状态良好，手续费远低于以太坊主网。适合日常 DeFi 操作。跨链到 Arbitrum 使用官方桥约需 10 分钟，第三方桥更快。"
    },
    "MATIC": {
        "network": "Polygon",
        "congestion": "低",
        "fee_range": "30-100 Gwei",
        "confirm_time": "~2 秒",
        "mempool_size": "~5,000 笔待确认",
        "advice": "Polygon 网络运行正常，手续费极低。适合日常交易和 DeFi 操作。从以太坊跨链到 Polygon 可使用官方桥（约 30 分钟）或第三方桥。"
    },
}

_DEFAULT_STATUS = {
    "network": "未知网络",
    "congestion": "未知",
    "fee_range": "未知",
    "confirm_time": "未知",
    "mempool_size": "未知",
    "advice": "暂不支持查询该链的网络状态。请确认链名称是否正确，当前支持：BTC、ETH、SOL、BSC、TRX、ARB、MATIC。"
}


def fetch_chain_status(chain: str) -> str:
    """获取指定区块链的网络状态，返回纯字符串。

    失败时返回用户可读的提示字符串（不抛异常），保证 Agent 调用安全。
    """
    chain_upper = chain.strip().upper()
    # 支持常见别名
    alias_map = {
        "BITCOIN": "BTC", "比特币": "BTC",
        "ETHEREUM": "ETH", "以太坊": "ETH",
        "SOLANA": "SOL",
        "BNB": "BSC", "BINANCE": "BSC", "币安": "BSC",
        "TRON": "TRX", "波场": "TRX",
        "ARBITRUM": "ARB",
        "POLYGON": "MATIC",
    }
    chain_upper = alias_map.get(chain_upper, chain_upper)

    status = _CHAIN_STATUS_DATA.get(chain_upper, _DEFAULT_STATUS)

    logger.info(f"[fetch_chain_status]查询链 {chain_upper} 网络状态，拥堵：{status['congestion']}")
    return (
        f"🔗 {status['network']} 模拟网络状态\n"
        f"- 网络拥堵：{status['congestion']}\n"
        f"- 手续费区间：{status['fee_range']}\n"
        f"- 预计确认时间：{status['confirm_time']}\n"
        f"- 内存池状态：{status['mempool_size']}\n"
        f"- 客服建议：{status['advice']}"
    )
