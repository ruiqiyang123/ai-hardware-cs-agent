import unittest

from agent.stream_policy import should_short_circuit_rag_answer


class StreamPolicyTest(unittest.TestCase):
    def test_short_circuits_successful_rag_tool_result(self):
        self.assertTrue(
            should_short_circuit_rag_answer(
                "rag_summarize",
                "请清洁充电触点。\n\n📚 参考来源：故障排除.txt",
            )
        )

    def test_does_not_short_circuit_non_rag_tool_result(self):
        self.assertFalse(should_short_circuit_rag_answer("get_weather", "深圳：26°C"))

    def test_does_not_short_circuit_empty_or_error_rag_result(self):
        self.assertFalse(should_short_circuit_rag_answer("rag_summarize", ""))
        self.assertFalse(
            should_short_circuit_rag_answer(
                "rag_summarize",
                "Error: InvalidDimensionException('Embedding dimension mismatch')",
            )
        )


if __name__ == "__main__":
    unittest.main()
