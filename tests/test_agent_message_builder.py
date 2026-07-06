import unittest

from agent.message_builder import build_agent_messages


class AgentMessageBuilderTest(unittest.TestCase):
    def test_appends_current_query_when_history_does_not_contain_it(self):
        messages = build_agent_messages(
            "扫地机器人无法回充怎么办？",
            [{"role": "assistant", "content": "你好"}],
        )

        self.assertEqual(
            messages,
            [
                {"role": "assistant", "content": "你好"},
                {"role": "user", "content": "扫地机器人无法回充怎么办？"},
            ],
        )

    def test_does_not_duplicate_current_query_when_history_already_contains_it(self):
        messages = build_agent_messages(
            "扫地机器人无法回充怎么办？",
            [{"role": "user", "content": "扫地机器人无法回充怎么办？"}],
        )

        self.assertEqual(messages, [{"role": "user", "content": "扫地机器人无法回充怎么办？"}])


if __name__ == "__main__":
    unittest.main()
