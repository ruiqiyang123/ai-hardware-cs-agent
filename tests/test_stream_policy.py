import unittest

from agent.stream_policy import should_short_circuit_rag_answer


class StreamPolicyTest(unittest.TestCase):
    def test_short_circuits_successful_rag_tool_result(self):
        self.assertTrue(
            should_short_circuit_rag_answer(
                "rag_summarize",
                "请先更换 USB-C 数据线并确认设备已解锁。\n\n📚 参考来源：故障排除.txt",
            )
        )

    def test_does_not_short_circuit_non_rag_tool_result(self):
        self.assertFalse(should_short_circuit_rag_answer("get_chain_status", "Ethereum 网络拥堵较高"))

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
