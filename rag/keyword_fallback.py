from pathlib import Path
from typing import List

from langchain_core.documents import Document


RECHARGE_QUERY_TERMS = ("回充", "充电座", "无法充电", "充电故障", "找不到充电")
RECHARGE_CONTENT_TERMS = ("回充", "充电座", "充电触点", "无法正常充电", "找不到充电座")
RECHARGE_FILES = ("故障排除.txt", "扫地机器人100问2.txt")


def _is_recharge_query(query: str) -> bool:
    return any(term in query for term in RECHARGE_QUERY_TERMS)


def _extract_relevant_lines(text: str, max_lines: int = 8) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    selected: List[str] = []

    for index, line in enumerate(lines):
        if not any(term in line for term in RECHARGE_CONTENT_TERMS):
            continue

        selected.append(line)
        if index + 1 < len(lines) and lines[index + 1].startswith("-"):
            selected.append(lines[index + 1])

        if len(selected) >= max_lines:
            break

    return "\n".join(selected[:max_lines])


def get_keyword_fallback_docs(query: str, data_dir: str) -> List[Document]:
    """Return high-confidence snippets for frequent after-sales keywords."""
    if not _is_recharge_query(query):
        return []

    docs: List[Document] = []
    base = Path(data_dir)
    for filename in RECHARGE_FILES:
        path = base / filename
        if not path.exists():
            continue

        content = _extract_relevant_lines(path.read_text(encoding="utf-8"))
        if content:
            docs.append(Document(page_content=content, metadata={"source": str(path)}))

    return docs
