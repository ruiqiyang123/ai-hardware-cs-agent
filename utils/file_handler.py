import hashlib
import os
import re
from typing import Optional

from utils.logger_handler import logger

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader


def get_file_md5_hex(filepath: str) -> Optional[str]:
    """获取文件 MD5 的十六进制字符串。"""
    if not os.path.exists(filepath):
        logger.error(f"[MD5计算]文件{filepath}不存在")
        return None
    if not os.path.isfile(filepath):
        logger.error(f"[MD5计算]路径{filepath}不是文件")
        return None

    md5_obj = hashlib.md5()
    chunk_size = 4096
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)

        return md5_obj.hexdigest()
    except Exception as e:
        logger.error(f"计算文件{filepath}md5失败，{str(e)}")
        return None


def listdir_with_allowed_type(path: str, allowed_types: tuple[str, ...]) -> tuple[str, ...]:
    """返回目录内允许后缀的文件路径。"""
    files = []
    if not os.path.isdir(path):
        logger.error(f"[lisdir_with_allowed_type]{path}不是文件夹")
        return tuple()

    for f in os.listdir(path):
        if f.endswith(allowed_types):
            files.append(os.path.join(path, f))
    return tuple(files)


def pdf_loader(filepath: str, passwd=None) -> list[Document]:
    return PyPDFLoader(filepath, passwd).load()


def _parse_source_backed_txt(filepath: str, text: str) -> list[Document]:
    """Parse KeyGuard source-backed TXT files into entry-level documents.

    Expected lightweight format:
    - First Markdown heading is the document title.
    - Source map lines use "- S1 Name: https://..."
    - Entries start with "1. 问题：..."
    - Each entry ends before the next numbered "问题" line.
    """
    if "资料来源" not in text or "来源参考" not in text:
        return []

    title_match = re.search(r"^#\s*(.+?)\s*$", text, flags=re.MULTILINE)
    doc_title = title_match.group(1).strip() if title_match else os.path.basename(filepath)

    source_map: dict[str, str] = {}
    for source_id, url in re.findall(r"^-\s*(S\d+)\s+.*?:\s*(https?://\S+)\s*$", text, flags=re.MULTILINE):
        source_map[source_id] = url.strip()

    entry_matches = list(re.finditer(r"^(\d+)\.\s*问题：(.+?)\s*$", text, flags=re.MULTILINE))
    if not entry_matches:
        return []

    documents: list[Document] = []
    for index, match in enumerate(entry_matches):
        entry_id = match.group(1)
        entry_question = match.group(2).strip()
        start = match.start()
        end = entry_matches[index + 1].start() if index + 1 < len(entry_matches) else len(text)
        entry_text = text[start:end].strip()

        refs_match = re.search(r"来源参考：(.+)", entry_text)
        source_ids: list[str] = []
        if refs_match:
            source_ids = re.findall(r"S\d+", refs_match.group(1))
        source_urls = [source_map[source_id] for source_id in source_ids if source_id in source_map]

        documents.append(
            Document(
                page_content=entry_text,
                metadata={
                    "source": filepath,
                    "doc_title": doc_title,
                    "entry_id": entry_id,
                    "entry_question": entry_question,
                    "source_ids": "、".join(source_ids),
                    "source_urls": " | ".join(source_urls),
                },
            )
        )

    return documents


def txt_loader(filepath: str) -> list[Document]:
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    source_backed_docs = _parse_source_backed_txt(filepath, text)
    if source_backed_docs:
        return source_backed_docs

    return TextLoader(filepath, encoding="utf-8").load()
