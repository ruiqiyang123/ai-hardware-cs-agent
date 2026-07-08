import tempfile
import unittest
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

from agent.react_agent import AgentToolContext, ReactAgent
from agent.services.memory_compression import MessageCompressionService
from database.profile_db import UserProfile
from utils.file_handler import listdir_with_allowed_type


class ReviewHardeningTest(unittest.TestCase):
    def test_listdir_with_allowed_type_returns_empty_tuple_for_missing_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_dir = Path(tmp) / "missing"

            files = listdir_with_allowed_type(str(missing_dir), ("txt", "pdf"))

        self.assertEqual(files, tuple())

    def test_compressed_summary_is_not_injected_as_user_turn(self):
        service = MessageCompressionService(max_turns=1)
        messages = [
            {"role": "user", "content": "第一个问题"},
            {"role": "assistant", "content": "第一个回答"},
            {"role": "user", "content": "第二个问题"},
            {"role": "assistant", "content": "第二个回答"},
        ]

        compressed = service.compress_messages(messages)

        self.assertEqual(compressed[0]["role"], "assistant")
        self.assertIn("不是用户新问题", compressed[0]["content"])
        self.assertEqual(compressed[-2:], messages[-2:])

    def test_context_tools_are_bound_to_execution_snapshot(self):
        context = AgentToolContext(
            user_id="1004",
            location="北京",
            profile=UserProfile(
                user_id="1004",
                experience_level="资深",
                region="北京",
                device_model="KeyGuard Max",
                preferred_chains="BTC, ETH",
                connection_method="USB-C",
                passphrase_enabled=True,
                backup_verified=True,
            ),
        )
        tools = {tool.name: tool for tool in ReactAgent._build_context_tools(context)}

        self.assertEqual(tools["get_user_id"].invoke({}), "1004")
        self.assertEqual(tools["get_user_location"].invoke({}), "北京")
        profile_text = tools["get_user_profile"].invoke({})
        self.assertIn("KeyGuard Max", profile_text)
        self.assertIn("Passphrase：已开启", profile_text)

    def test_streaming_ignores_compressed_history_summary_as_final_answer(self):
        class FakeGraph:
            def stream(self, input_dict, stream_mode):
                returned_messages = []
                for index, item in enumerate(input_dict["messages"]):
                    if item["role"] == "assistant":
                        returned_messages.append(AIMessage(content=item["content"], id=f"history-{index}"))
                    else:
                        returned_messages.append(HumanMessage(content=item["content"], id=f"history-{index}"))
                returned_messages.append(AIMessage(content="这是针对当前问题的新回答", id="new-answer"))
                yield {"messages": returned_messages}

        class FakeReactAgent(ReactAgent):
            def _build_agent(self, context):
                return FakeGraph()

        agent = FakeReactAgent(chat_model=object(), max_turns=1)

        events = list(
            agent.execute_stream(
                "第三个问题",
                [
                    {"role": "user", "content": "第一个问题"},
                    {"role": "assistant", "content": "第一个回答"},
                    {"role": "user", "content": "第二个问题"},
                    {"role": "assistant", "content": "第二个回答"},
                ],
            )
        )

        self.assertEqual(events, [("answer", "这是针对当前问题的新回答")])


if __name__ == "__main__":
    unittest.main()
