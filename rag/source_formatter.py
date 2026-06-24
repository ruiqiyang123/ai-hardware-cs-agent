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
    """把多份文档的元数据格式化成「参考来源：a、b、c」的引用行。

    按首次出现顺序去重，避免同一文档被多次命中时重复列出。
    """
    unique_sources = []
    for metadata in metadata_list:
        name = extract_source_name(metadata)
        if name not in unique_sources:
            unique_sources.append(name)
    return "参考来源：" + "、".join(unique_sources)
