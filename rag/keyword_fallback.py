from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from utils.file_handler import txt_loader


FALLBACK_RULES = [
    {
        "query_terms": (
            "开不了机",
            "无法开机",
            "屏幕不亮",
            "屏幕没显示",
            "按键无响应",
            "卡死",
            "无响应",
        ),
        "content_terms": (
            "开不了机",
            "屏幕",
            "按键",
            "卡死",
            "重启",
            "USB-C",
            "电源",
            "长按",
        ),
        "files": ("故障排除.txt", "固件升级.txt"),
    },
    {
        "query_terms": (
            "蓝牙",
            "配对失败",
            "配对不上",
            "未发现设备",
            "手机连接失败",
        ),
        "content_terms": (
            "蓝牙",
            "配对",
            "旧配对",
            "权限",
            "重新配对",
        ),
        "files": ("故障排除.txt", "安全使用指南.txt"),
    },
    {
        "query_terms": (
            "连接不上",
            "无法连接",
            "识别不到",
            "未发现设备",
            "USB",
            "USB-C",
            "数据线",
            "电脑",
            "线缆",
        ),
        "content_terms": (
            "连接",
            "无法识别",
            "USB-C",
            "数据线",
            "USB Hub",
            "端口",
            "驱动",
            "设备已解锁",
            "官方应用",
        ),
        "files": ("故障排除.txt", "安全使用指南.txt"),
    },
    {
        "query_terms": ("锁定", "PIN", "忘记 PIN", "输错", "解锁"),
        "content_terms": ("PIN", "锁定", "重置", "备份", "恢复", "客服不能索要"),
        "files": ("故障排除.txt", "助记词与备份.txt"),
    },
    {
        "query_terms": ("助记词泄露", "助记词被看到", "助记词丢了", "私钥泄露", "恢复钱包"),
        "content_terms": ("助记词", "泄露", "立即", "转移资产", "恢复钱包", "安全边界"),
        "files": ("助记词与备份.txt", "安全使用指南.txt"),
    },
    {
        "query_terms": ("固件升级", "升级失败", "升级中断", "固件", "版本"),
        "content_terms": ("固件", "升级", "官方", "断开连接", "备份", "恢复模式"),
        "files": ("固件升级.txt", "故障排除.txt"),
    },
    {
        "query_terms": ("交易未确认", "pending", "手续费", "Gas", "nonce", "转账很慢"),
        "content_terms": ("交易", "未确认", "手续费", "Gas", "nonce", "区块浏览器"),
        "files": ("交易与链网络.txt", "安全使用指南.txt"),
    },
]


def _matching_rule(query: str) -> Optional[dict]:
    normalized = query.lower()
    for rule in FALLBACK_RULES:
        if any(term.lower() in normalized for term in rule["query_terms"]):
            return rule
    return None


def _extract_relevant_lines(text: str, terms: tuple[str, ...], max_lines: int = 8) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    selected: List[str] = []

    for index, line in enumerate(lines):
        if not any(term.lower() in line.lower() for term in terms):
            continue

        selected.append(line)
        if index + 1 < len(lines) and lines[index + 1].startswith(("建议动作", "排查步骤", "-")):
            selected.append(lines[index + 1])

        if len(selected) >= max_lines:
            break

    return "\n".join(selected[:max_lines])


def get_keyword_fallback_docs(query: str, data_dir: str) -> List[Document]:
    """Return high-confidence snippets for frequent hardware wallet support keywords."""
    rule = _matching_rule(query)
    if not rule:
        return []

    docs: List[Document] = []
    base = Path(data_dir)
    for filename in rule["files"]:
        path = base / filename
        if not path.exists():
            continue

        loaded_docs = txt_loader(str(path))
        for loaded_doc in loaded_docs:
            content = _extract_relevant_lines(loaded_doc.page_content, rule["content_terms"])
            if content:
                docs.append(Document(page_content=content, metadata=dict(loaded_doc.metadata)))
                break

    return docs
