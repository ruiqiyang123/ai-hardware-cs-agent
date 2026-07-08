import unittest
import tempfile
from pathlib import Path

from rag.source_formatter import extract_source_name, format_reference_sources
from utils.file_handler import txt_loader


class RagSourcesTest(unittest.TestCase):
    def test_extract_source_name_supports_absolute_and_missing_sources(self):
        self.assertEqual(extract_source_name({"source": "/tmp/data/故障排除.txt"}), "故障排除.txt")
        self.assertEqual(extract_source_name({"source": "data/维护保养.txt"}), "维护保养.txt")
        self.assertEqual(extract_source_name({}), "未知来源")

    def test_format_reference_sources_deduplicates_in_order(self):
        metadata_list = [
            {"source": "/tmp/data/故障排除.txt"},
            {"source": "/tmp/data/维护保养.txt"},
            {"source": "/tmp/data/故障排除.txt"},
        ]

        self.assertEqual(format_reference_sources(metadata_list), "参考来源：故障排除.txt、维护保养.txt")

    def test_txt_loader_extracts_source_backed_entry_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "故障排除.txt"
            path.write_text(
                """# 硬件钱包设备故障排除（source-backed 改写）

资料来源（事实参考，内容已重新组织为 KeyGuard 客服条目，不复制原文）：
- S1 Ledger Support - Fix USB connection issues: https://support.ledger.com/article/115005165269-zd
- S2 Ledger Support - Fix Bluetooth pairing issues: https://support.ledger.com/article/360025864773-zd

1. 问题：蓝牙无法连接、配对失败或频繁断开。
适用场景：手机 App 一直显示未发现设备。
排查步骤：删除旧配对记录后重新配对。
来源参考：S2

2. 问题：电脑识别不到硬件钱包。
排查步骤：更换 USB-C 数据线。
来源参考：S1
""",
                encoding="utf-8",
            )

            docs = txt_loader(str(path))

        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].metadata["doc_title"], "硬件钱包设备故障排除（source-backed 改写）")
        self.assertEqual(docs[0].metadata["entry_id"], "1")
        self.assertEqual(docs[0].metadata["entry_question"], "蓝牙无法连接、配对失败或频繁断开。")
        self.assertEqual(docs[0].metadata["source_ids"], "S2")
        self.assertEqual(docs[0].metadata["source_urls"], "https://support.ledger.com/article/360025864773-zd")

    def test_format_reference_sources_only_shows_entry_references(self):
        metadata_list = [
            {
                "source": "/tmp/data/故障排除.txt",
                "entry_id": "1",
                "entry_question": "硬件钱包开不了机、屏幕没有显示。",
                "source_ids": "S1",
                "source_urls": "https://support.ledger.com/article/115005165269-zd",
            },
            {
                "source": "/tmp/data/固件升级.txt",
                "entry_id": "7",
                "entry_question": "设备进入恢复模式或 bootloader 模式。",
                "source_ids": "S3",
                "source_urls": "https://trezor.io/support/troubleshooting/device-issues/firmware-update-issues",
            },
        ]

        formatted = format_reference_sources(metadata_list)

        self.assertEqual(
            formatted,
            "参考来源：故障排除.txt 第1条「硬件钱包开不了机、屏幕没有显示。」、"
            "固件升级.txt 第7条「设备进入恢复模式或 bootloader 模式。」",
        )
        self.assertNotIn("官方/标准来源", formatted)
        self.assertNotIn("https://", formatted)
        self.assertNotIn("S1", formatted)


if __name__ == "__main__":
    unittest.main()
