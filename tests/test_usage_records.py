import tempfile
import textwrap
import unittest
from pathlib import Path

from agent.services.usage_records import fetch_usage_record, find_usage_record, load_usage_records


class UsageRecordsTest(unittest.TestCase):
    def test_load_usage_records_handles_quoted_commas_and_newlines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.csv"
            path.write_text(
                textwrap.dedent(
                    '''\
                    用户ID,使用概况,安全状态,交易状态,风险对比,时间
                    1001,"签名次数:18
                    常用链:ETH,BTC","固件:已是最新版,备份:已验证","失败交易:1笔","风险操作低于65%同类用户",2025-06
                    '''
                ),
                encoding="utf-8",
            )

            records = load_usage_records(str(path))

        self.assertEqual(records["1001"]["2025-06"]["特征"], "签名次数:18\n常用链:ETH,BTC")
        self.assertEqual(records["1001"]["2025-06"]["效率"], "固件:已是最新版,备份:已验证")

    def test_fetch_usage_record_returns_empty_string_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.csv"
            path.write_text(
                "用户ID,使用概况,安全状态,交易状态,风险对比,时间\n"
                "1001,签名次数:18,固件:已是最新版,失败交易:1笔,风险操作低于65%同类用户,2025-06\n",
                encoding="utf-8",
            )

            self.assertIn("签名次数", fetch_usage_record(str(path), "1001", "2025-06"))
            self.assertEqual(fetch_usage_record(str(path), "1001", "2025-07"), "")

    def test_find_usage_record_can_fallback_to_latest_available_month(self):
        records = {
            "1001": {
                "2026-05": {"特征": "签名次数:12", "效率": "固件:需升级", "耗材": "失败交易:2笔", "对比": "风险操作低于55%同类用户"},
                "2026-06": {"特征": "签名次数:18", "效率": "固件:已是最新版", "耗材": "失败交易:1笔", "对比": "风险操作低于70%同类用户"},
            }
        }

        result = find_usage_record(records, "1001", "2026-07", fallback_to_latest=True)

        self.assertIn("签名次数:18", result)
        self.assertIn("数据说明", result)
        self.assertIn("2026-07", result)
        self.assertIn("2026-06", result)


if __name__ == "__main__":
    unittest.main()
