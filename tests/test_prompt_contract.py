import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PromptContractTest(unittest.TestCase):
    def test_main_prompt_limits_regular_rag_questions_to_one_retrieval(self):
        prompt = (ROOT / "prompts" / "main_prompt.txt").read_text(encoding="utf-8")

        self.assertIn("普通知识库问答最多调用一次 rag_summarize", prompt)
        self.assertIn("拿到 rag_summarize 返回后必须直接生成最终回答", prompt)


if __name__ == "__main__":
    unittest.main()
