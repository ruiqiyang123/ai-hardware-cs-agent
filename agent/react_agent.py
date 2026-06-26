from typing import Iterator, Tuple, List, Dict

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from model.factory import chat_model as _default_chat_model
from agent.tools.agent_tools import (rag_summarize, get_weather, get_user_location, get_user_id,
                                     get_current_month, fetch_external_data, fill_context_for_report)
from agent.tools.profile_tools import get_user_profile
from agent.tools.middleware import build_agent_prompt
from agent.services.memory_compression import MessageCompressionService


# 流式输出事件类型，前端按此分类渲染：
#   ("thought", str)   - Agent 中间思考文本（折叠展示）
#   ("tool_call", str) - Agent 调用某个工具（折叠展示）
#   ("tool_result", str) - 工具返回的内容（折叠展示）
#   ("answer", str)    - Agent 最终回答（chat 区主流式输出）
StreamEvent = Tuple[str, str]


class ReactAgent:
    def __init__(self, chat_model=None, max_turns: int = 6):
        """构建 ReAct Agent。

        Args:
            chat_model: 可选，按会话注入的 chat 模型（Web 前端通过 build_chat_model 构建）。
                        未传则使用模块级默认实例（基于环境变量，供 CLI / 评测脚本使用）。
            max_turns: 滑动窗口保留的最大对话轮数（默认 6 轮），超过后自动压缩旧对话。
        """
        self.agent = create_react_agent(
            model=chat_model or _default_chat_model,
            tools=[rag_summarize, get_weather, get_user_location, get_user_id,
                   get_current_month, fetch_external_data, fill_context_for_report,
                   get_user_profile],
            prompt=build_agent_prompt,
            version="v2",
        )
        self.compression_service = MessageCompressionService(max_turns=max_turns)

    def execute_stream(self, query: str, chat_history: List[Dict[str, str]] = None) -> Iterator[StreamEvent]:
        """流式执行，按事件类型 yield。

        改造前：所有 AIMessage 都 yield 为字符串，"思考: xxx"和最终回答混在一起
        污染对话流。改造后区分四类事件，前端可分区渲染：思考/工具调用折叠展示，
        最终回答独占 chat 区。

        Args:
            query: 用户当前输入的问题
            chat_history: 历史对话列表，格式为 [{"role": "user", "content": "..."}, ...]
        """
        # 构建输入消息（历史 + 当前问题）
        messages = list(chat_history or [])  # 复制避免修改原列表
        messages.append({"role": "user", "content": query})

        # 压缩消息（如果超过阈值）
        compressed_messages = self.compression_service.compress_messages(messages)

        input_dict = {
            "messages": compressed_messages
        }

        seen_ai_ids: set[str] = set()
        seen_tool_ids: set[str] = set()

        all_chunks = list(self.agent.stream(input_dict, stream_mode="values"))
        if not all_chunks:
            return

        # 最后一帧的最后一条 AIMessage 才是最终回答；前面所有 AIMessage 都是中间思考
        final_chunk = all_chunks[-1]
        final_messages = final_chunk.get("messages", [])
        final_answer_id = None
        for msg in reversed(final_messages):
            if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
                final_answer_id = getattr(msg, "id", None)
                break

        for chunk in all_chunks:
            for msg in chunk.get("messages", []):
                msg_id = getattr(msg, "id", None)
                if not msg_id:
                    continue

                if isinstance(msg, AIMessage):
                    if msg_id in seen_ai_ids:
                        continue
                    seen_ai_ids.add(msg_id)

                    content = (msg.content or "").strip()
                    tool_calls = getattr(msg, "tool_calls", None) or []

                    # 最终回答：仅最后一条无 tool_call 的 AIMessage
                    if msg_id == final_answer_id:
                        if content:
                            yield ("answer", content)
                    else:
                        # 中间思考：可能伴随工具调用
                        if content:
                            yield ("thought", content)
                        for tc in tool_calls:
                            tool_name = tc.get("name", "unknown")
                            tool_args = tc.get("args", {})
                            yield ("tool_call", f"调用 `{tool_name}`，参数：{tool_args}")

                elif isinstance(msg, ToolMessage):
                    if msg_id in seen_tool_ids:
                        continue
                    seen_tool_ids.add(msg_id)
                    tool_name = getattr(msg, "name", "tool")
                    tool_output = (msg.content or "").strip()
                    # 工具结果可能很长，截断展示
                    preview = tool_output if len(tool_output) <= 400 else tool_output[:400] + "...(已截断)"
                    yield ("tool_result", f"`{tool_name}` 返回：{preview}")


if __name__ == '__main__':
    agent = ReactAgent()

    for kind, content in agent.execute_stream("给我生成我的使用报告"):
        if kind == "answer":
            print("\n=== 最终回答 ===\n" + content)
        else:
            print(f"[{kind}] {content}")
