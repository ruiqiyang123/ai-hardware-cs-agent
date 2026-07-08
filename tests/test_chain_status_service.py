import unittest

from agent.services.chain_status_service import fetch_chain_status


class ChainStatusServiceTest(unittest.TestCase):
    def test_fetch_chain_status_returns_known_chain_guidance(self):
        result = fetch_chain_status("ETH")

        self.assertIn("Ethereum", result)
        self.assertIn("手续费区间", result)
        self.assertIn("预计确认时间", result)
        self.assertIn("客服建议", result)

    def test_fetch_chain_status_supports_common_aliases(self):
        result = fetch_chain_status("以太坊")

        self.assertIn("Ethereum", result)
        self.assertIn("Gas", result)

    def test_fetch_chain_status_reports_unknown_chain(self):
        result = fetch_chain_status("unknown-chain")

        self.assertIn("暂不支持查询该链", result)
        self.assertIn("BTC", result)


if __name__ == "__main__":
    unittest.main()
