import unittest

from eval.run_eval import run_agent, score_answer


class FakeEventAgent:
    def execute_stream(self, question: str):
        return iter([
            ("thought", "需要先检索知识库"),
            ("tool_call", "调用 `rag_summarize`"),
            ("tool_result", "命中故障排除资料"),
            ("answer", "请先检查充电座，"),
            ("answer", "再清洁红外传感器。"),
        ])


class EvalScoringTest(unittest.TestCase):
    def test_score_answer_reports_hits_misses_and_coverage(self):
        score = score_answer("请检查充电座、基座和红外传感器。", ["充电座", "基座", "传感器", "重启"])

        self.assertEqual(score["coverage"], 0.75)
        self.assertEqual(score["hit_keywords"], ["充电座", "基座", "传感器"])
        self.assertEqual(score["missed_keywords"], ["重启"])

    def test_score_answer_handles_empty_expected_keywords(self):
        score = score_answer("任意回答", [])

        self.assertEqual(score["coverage"], 0)
        self.assertEqual(score["hit_keywords"], [])
        self.assertEqual(score["missed_keywords"], [])

    def test_run_agent_only_collects_answer_events(self):
        answer = run_agent(FakeEventAgent(), "扫地机器人无法正常回充怎么办？")

        self.assertEqual(answer, "请先检查充电座，再清洁红外传感器。")


if __name__ == "__main__":
    unittest.main()
