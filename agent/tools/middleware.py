from langchain_core.messages import BaseMessage, SystemMessage
from utils.prompt_loader import load_system_prompts, load_report_prompts
from utils.logger_handler import logger


REPORT_TRIGGER_TEXT = "fill_context_for_report已调用"


def _message_text(message: BaseMessage) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    return str(content)


def is_report_context(messages: list[BaseMessage]) -> bool:
    """判断当前消息链路是否进入报告生成场景。"""
    for message in messages:
        name = getattr(message, "name", "")
        text = _message_text(message)
        if name == "fill_context_for_report" or REPORT_TRIGGER_TEXT in text:
            return True
    return False


def build_agent_prompt(state: dict) -> list[BaseMessage]:
    """为 LangGraph ReAct Agent 构建动态系统提示词。"""
    messages = list(state.get("messages", []))
    prompt_text = load_report_prompts() if is_report_context(messages) else load_system_prompts()
    logger.info(f"[agent prompt]当前消息数：{len(messages)}，报告模式：{is_report_context(messages)}")
    return [SystemMessage(content=prompt_text), *messages]
