from dataclasses import dataclass
from typing import Iterator, Tuple, List, Dict, Optional

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from model.factory import chat_model as _default_chat_model
from database.profile_db import UserProfile
from agent.tools.agent_tools import (
    rag_summarize,
    get_chain_status,
    get_current_month,
    fetch_external_data,
    fill_context_for_report,
    resolve_location_or_ip,
)
from agent.tools.profile_tools import format_user_profile
from agent.tools.middleware import build_agent_prompt
from agent.services.memory_compression import MessageCompressionService
from agent.message_builder import build_agent_messages
from agent.stream_policy import should_short_circuit_rag_answer
from utils.session_context import DEFAULT_USER_ID, current_location, current_user_id
from utils.user_profile import current_profile


# 流式输出事件类型，前端按此分类渲染：
#   ("thought", str)   - Agent 中间思考文本（折叠展示）
#   ("tool_call", str) - Agent 调用某个工具（折叠展示）
#   ("tool_result", str) - 工具返回的内容（折叠展示）
#   ("answer", str)    - Agent 最终回答（chat 区主流式输出）
StreamEvent = Tuple[str, str]


@dataclass(frozen=True)
class AgentToolContext:
    user_id: str = DEFAULT_USER_ID
    location: Optional[str] = None
    profile: Optional[UserProfile] = None


class ReactAgent:
    def __init__(self, chat_model=None, max_turns: int = 6):
        """构建 ReAct Agent。

        Args:
            chat_model: 可选，按会话注入的 chat 模型（Web 前端通过 build_chat_model 构建）。
                        未传则使用模块级默认实例（基于环境变量，供 CLI / 评测脚本使用）。
            max_turns: 滑动窗口保留的最大对话轮数（默认 6 轮），超过后自动压缩旧对话。
        """
        self.chat_model = chat_model or _default_chat_model
        self.compression_service = MessageCompressionService(max_turns=max_turns)

    @staticmethod
    def _build_context_tools(context: AgentToolContext):
        """构造绑定本次会话快照的工具，避免多用户 Streamlit 会话串号。"""

        @tool(description="获取当前用户所在地区，返回纯字符串地区名。优先使用前端设置的会话地区，兜底用 IP 粗定位")
        def get_user_location() -> str:
            return resolve_location_or_ip(context.location)

        @tool(description="获取当前登录用户的ID，返回纯字符串。ID 来自本次 Agent 执行的会话快照")
        def get_user_id() -> str:
            return context.user_id

        @tool(description="获取当前用户的档案信息（经验等级、地区、设备型号、常用链、连接方式、是否开启 Passphrase、是否完成备份验证），返回结构化字符串")
        def get_user_profile() -> str:
            return format_user_profile(context.profile)

        return [
            rag_summarize,
            get_chain_status,
            get_user_location,
            get_user_id,
            get_current_month,
            fetch_external_data,
            fill_context_for_report,
            get_user_profile,
        ]

    def _build_agent(self, context: AgentToolContext):
        return create_react_agent(
            model=self.chat_model,
            tools=self._build_context_tools(context),
            prompt=build_agent_prompt,
            version="v2",
        )

    def execute_stream(
        self,
        query: str,
        chat_history: List[Dict[str, str]] = None,
        user_id: Optional[str] = None,
        location: Optional[str] = None,
        user_profile: Optional[UserProfile] = None,
    ) -> Iterator[StreamEvent]:
        """流式执行，按事件类型 yield。

        改造前：所有 AIMessage 都 yield 为字符串，"思考: xxx"和最终回答混在一起
        污染对话流。改造后区分四类事件，前端可分区渲染：思考/工具调用折叠展示，
        最终回答独占 chat 区。

        Args:
            query: 用户当前输入的问题
            chat_history: 历史对话列表，格式为 [{"role": "user", "content": "..."}, ...]
            user_id: 可选，本次执行绑定的用户 ID。Web 前端应显式传入，避免共享进程串号。
            location: 可选，本次执行绑定的地区。
            user_profile: 可选，本次执行绑定的用户档案。
        """
        context = AgentToolContext(
            user_id=user_id or current_user_id(),
            location=location if location is not None else current_location(),
            profile=user_profile if user_profile is not None else current_profile(),
        )
        agent = self._build_agent(context)

        # 构建输入消息（历史 + 当前问题），兼容前端已将当前问题写入历史的场景。
        messages = build_agent_messages(query, chat_history)

        # 压缩消息（如果超过阈值）
        compressed_messages = self.compression_service.compress_messages(messages)

        input_dict = {
            "messages": compressed_messages
        }

        seen_ai_ids: set[str] = set()
        seen_tool_ids: set[str] = set()
        # stream_mode="values" returns the full state each time; skip input history.
        processed_message_count = len(compressed_messages)

        for chunk in agent.stream(input_dict, stream_mode="values"):
            state_messages = chunk.get("messages", [])
            new_messages = state_messages[processed_message_count:]
            processed_message_count = max(processed_message_count, len(state_messages))

            for msg in new_messages:
                msg_id = getattr(msg, "id", None)
                if not msg_id:
                    continue

                if isinstance(msg, AIMessage):
                    if msg_id in seen_ai_ids:
                        continue
                    seen_ai_ids.add(msg_id)

                    content = (msg.content or "").strip()
                    tool_calls = getattr(msg, "tool_calls", None) or []

                    # 无 tool_call 的 AIMessage 视为最终回答。RAG 场景会在 ToolMessage
                    # 返回时更早收口，避免 MiMo 重复检索或误走无关工具。
                    if not tool_calls:
                        if content:
                            yield ("answer", content)
                            return
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
                    if should_short_circuit_rag_answer(tool_name, tool_output):
                        yield ("answer", tool_output)
                        return


if __name__ == '__main__':
    agent = ReactAgent()

    for kind, content in agent.execute_stream("给我生成我的使用报告"):
        if kind == "answer":
            print("\n=== 最终回答 ===\n" + content)
        else:
            print(f"[{kind}] {content}")
