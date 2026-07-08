import tempfile
import unittest
from pathlib import Path

from rag.keyword_fallback import get_keyword_fallback_docs


class KeywordFallbackTest(unittest.TestCase):
    def test_returns_connection_docs_for_connection_queries(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "故障排除.txt").write_text(
                "1. 故障现象：App 无法识别硬件钱包；排查步骤：更换 USB-C 数据线，确认设备已解锁。\n",
                encoding="utf-8",
            )
            (data_dir / "安全使用指南.txt").write_text(
                "2. 适用场景：连接设备时的安全边界；建议动作：只使用官方应用，不要输入助记词或 PIN。\n",
                encoding="utf-8",
            )

            docs = get_keyword_fallback_docs("硬件钱包连接不上电脑，该怎么排查？", str(data_dir))

        self.assertEqual(len(docs), 2)
        self.assertIn("无法识别硬件钱包", docs[0].page_content)
        self.assertEqual(docs[0].metadata["source"], str(data_dir / "故障排除.txt"))
        self.assertIn("不要输入助记词", docs[1].page_content)

    def test_returns_no_docs_for_unrelated_queries(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = get_keyword_fallback_docs("今天午饭吃什么？", tmp)

        self.assertEqual(docs, [])

    def test_preserves_source_backed_metadata_for_bluetooth_queries(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "故障排除.txt").write_text(
                """# 硬件钱包设备故障排除（source-backed 改写）

资料来源（事实参考，内容已重新组织为 KeyGuard 客服条目，不复制原文）：
- S1 Ledger Support - Fix Bluetooth pairing issues: https://support.ledger.com/article/360025864773-zd

1. 问题：蓝牙无法连接、配对失败或频繁断开。
排查步骤：删除旧配对记录，打开蓝牙权限后重新配对。
来源参考：S1
""",
                encoding="utf-8",
            )

            docs = get_keyword_fallback_docs("蓝牙没法连接手机怎么办？", str(data_dir))

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].metadata["entry_id"], "1")
        self.assertEqual(docs[0].metadata["source_ids"], "S1")
        self.assertIn("360025864773", docs[0].metadata["source_urls"])


if __name__ == "__main__":
    unittest.main()
