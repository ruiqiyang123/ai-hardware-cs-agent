"""RAG 引用来源格式化工具。

把这里从 rag_service.py 里抽出来的原因：
- 来源提取/去重/拼接是纯逻辑，不依赖向量库或 LLM，单独成模块后可独立单测；
- rag_service.py 只负责检索+总结，引用格式化交给本模块，职责更清晰。
"""
import os


def extract_source_name(metadata: dict) -> str:
    """从文档元数据中提取人类可读的来源名（文件名）。

    LangChain 加载文档时，metadata['source'] 通常是文件绝对路径，
    这里只取文件名展示给用户。兼容 / 和 os.sep 两种分隔符。
    """
    source = metadata.get("source", "未知来源")
    if source and os.sep in source:
        source = source.rsplit(os.sep, 1)[-1]
    elif source and "/" in source:
        source = source.rsplit("/", 1)[-1]
    return source


def format_reference_sources(metadata_list: list[dict]) -> str:
    """把多份文档的元数据格式化成引用行。

    优先使用 source-backed 条目 metadata，展示文件和命中条目；
    旧文档则退化为文件名。按首次出现顺序去重。
    """
    unique_entries = []
    seen_entries = set()

    for metadata in metadata_list:
        name = extract_source_name(metadata)
        entry_id = metadata.get("entry_id")
        entry_question = metadata.get("entry_question")

        if entry_id and entry_question:
            label = f"{name} 第{entry_id}条「{entry_question}」"
            dedupe_key = (name, entry_id)
        else:
            label = name
            dedupe_key = (name, None)

        if dedupe_key not in seen_entries:
            seen_entries.add(dedupe_key)
            unique_entries.append(label)

    return "参考来源：" + "、".join(unique_entries[:5])
