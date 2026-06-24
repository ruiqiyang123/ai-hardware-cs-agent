import unittest

from eval.run_eval import score_answer


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


if __name__ == "__main__":
    unittest.main()
