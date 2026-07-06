import tempfile
import unittest
from pathlib import Path

from rag.keyword_fallback import get_keyword_fallback_docs


class KeywordFallbackTest(unittest.TestCase):
    def test_returns_charging_docs_for_recharge_queries(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "故障排除.txt").write_text(
                "10. 故障现象：机器人找不到充电座；检测：充电座周围是否有遮挡；修复：清理障碍物。\n",
                encoding="utf-8",
            )
            (data_dir / "扫地机器人100问2.txt").write_text(
                "3. **机器人找不到充电座怎么处理？**\n- 清理充电座周围障碍物，保证前方无遮挡。\n",
                encoding="utf-8",
            )

            docs = get_keyword_fallback_docs("扫地机器人无法正常回充，该怎么排查？", str(data_dir))

        self.assertEqual(len(docs), 2)
        self.assertIn("找不到充电座", docs[0].page_content)
        self.assertEqual(docs[0].metadata["source"], str(data_dir / "故障排除.txt"))
        self.assertIn("前方无遮挡", docs[1].page_content)

    def test_returns_no_docs_for_unrelated_queries(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = get_keyword_fallback_docs("小户型怎么选扫地机器人？", tmp)

        self.assertEqual(docs, [])


if __name__ == "__main__":
    unittest.main()
