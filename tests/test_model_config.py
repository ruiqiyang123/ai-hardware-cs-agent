import unittest

from utils.model_config import DEFAULT_EMBEDDING_PROVIDER, DEFAULT_MIMO_CHAT_MODEL, build_chat_config


class ModelConfigTest(unittest.TestCase):
    def test_mimo_config_uses_token_plan_default_model(self):
        config = build_chat_config(
            provider="mimo",
            dashscope_key="expired-dashscope-key",
            mimo_key="tp-secret-key",
            mimo_base_url=None,
            mimo_model_name=None,
        )

        self.assertTrue(config.is_configured)
        self.assertEqual(config.kwargs["provider"], "mimo")
        self.assertEqual(config.kwargs["model_name"], DEFAULT_MIMO_CHAT_MODEL)
        self.assertEqual(DEFAULT_MIMO_CHAT_MODEL, "tmimo-v2.5-pro")

    def test_signature_does_not_contain_raw_api_key(self):
        config = build_chat_config(
            provider="mimo",
            dashscope_key=None,
            mimo_key="tp-secret-key",
            mimo_base_url="https://token-plan-sgp.xiaomimimo.com/v1",
            mimo_model_name="tmimo-v2.5-pro",
        )

        self.assertIn("mimo:", config.signature)
        self.assertNotIn("tp-secret-key", config.signature)

    def test_selected_dashscope_does_not_get_overridden_by_mimo_key(self):
        config = build_chat_config(
            provider="dashscope",
            dashscope_key="dashscope-key",
            mimo_key="tp-secret-key",
            mimo_base_url=None,
            mimo_model_name=None,
        )

        self.assertTrue(config.is_configured)
        self.assertEqual(config.kwargs["provider"], "dashscope")
        self.assertEqual(config.kwargs["api_key"], "dashscope-key")

    def test_missing_selected_provider_key_is_unconfigured(self):
        config = build_chat_config(
            provider="mimo",
            dashscope_key="dashscope-key",
            mimo_key="",
            mimo_base_url=None,
            mimo_model_name=None,
        )

        self.assertFalse(config.is_configured)
        self.assertEqual(config.kwargs, {})

    def test_default_embedding_provider_runs_without_dashscope_key(self):
        self.assertEqual(DEFAULT_EMBEDDING_PROVIDER, "local")


if __name__ == "__main__":
    unittest.main()
