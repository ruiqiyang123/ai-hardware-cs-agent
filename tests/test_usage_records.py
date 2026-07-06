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
                    用户ID,特征,清洁效率,耗材,对比,时间
                    1001,"覆盖率:88%
                    日均清扫:42㎡","清扫效率:90%,稳定","HEPA滤网:剩余70%","优于65%同面积用户",2025-06
                    '''
                ),
                encoding="utf-8",
            )

            records = load_usage_records(str(path))

        self.assertEqual(records["1001"]["2025-06"]["特征"], "覆盖率:88%\n日均清扫:42㎡")
        self.assertEqual(records["1001"]["2025-06"]["效率"], "清扫效率:90%,稳定")

    def test_fetch_usage_record_returns_empty_string_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.csv"
            path.write_text(
                "用户ID,特征,清洁效率,耗材,对比,时间\n"
                "1001,覆盖率:88%,清扫效率:90%,HEPA滤网:剩余70%,优于65%同面积用户,2025-06\n",
                encoding="utf-8",
            )

            self.assertIn("覆盖率", fetch_usage_record(str(path), "1001", "2025-06"))
            self.assertEqual(fetch_usage_record(str(path), "1001", "2025-07"), "")

    def test_find_usage_record_can_fallback_to_latest_available_month(self):
        records = {
            "1001": {
                "2026-05": {"特征": "覆盖率:86%", "效率": "清扫效率:81%", "耗材": "HEPA滤网:剩余52%", "对比": "优于65%同面积用户"},
                "2026-06": {"特征": "覆盖率:88%", "效率": "清扫效率:90%", "耗材": "HEPA滤网:剩余70%", "对比": "优于70%同面积用户"},
            }
        }

        result = find_usage_record(records, "1001", "2026-07", fallback_to_latest=True)

        self.assertIn("覆盖率:88%", result)
        self.assertIn("数据说明", result)
        self.assertIn("2026-07", result)
        self.assertIn("2026-06", result)


if __name__ == "__main__":
    unittest.main()
