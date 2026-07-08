"""
消息压缩服务：当对话历史超过阈值时，自动压缩旧消息为摘要

参考 Claude Code 的滑动窗口机制，保持最近 N 轮完整对话，
将更早的对话压缩为摘要，控制 token 成本。
"""

from typing import List, Dict
from utils.logger_handler import logger


class MessageCompressionService:
    def __init__(self, max_turns: int = 6):
        """
        Args:
            max_turns: 保留的最大对话轮数（默认 6 轮 = 12 条消息）
        """
        self.max_turns = max_turns

    def should_compress(self, messages: List[Dict[str, str]]) -> bool:
        """判断是否需要压缩消息"""
        # 只统计 user 消息数量（代表对话轮数），
        # 避免压缩后插入的摘要消息（非 user/assistant 配对）干扰计数。
        user_count = sum(1 for m in messages if m.get("role") == "user")
        return user_count > self.max_turns

    def compress_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        压缩消息历史：
        1. 保留最近 max_turns 轮完整对话
        2. 将旧对话压缩为一条摘要消息
        3. 返回压缩后的消息列表

        Args:
            messages: 消息列表，每条消息格式为 {"role": "user|assistant", "content": "..."}

        Returns:
            压缩后的消息列表：[摘要消息, 保留的最近对话...]
        """
        if not self.should_compress(messages):
            return messages

        # 计算分割点
        total_messages = len(messages)
        keep_count = self.max_turns * 2  # 保留的消息数

        # 旧消息用于压缩
        old_messages = messages[:total_messages - keep_count]
        # 新消息完整保留
        new_messages = messages[total_messages - keep_count:]

        # 生成摘要
        summary = self._generate_summary(old_messages)

        # 构建压缩后的消息列表
        compressed = [
            {
                # 用 assistant 角色承载摘要，避免模型把摘要误解为用户的新问题。
                # 不用 system 角色是为了避免和 build_agent_prompt 注入的系统消息冲突。
                "role": "assistant",
                "content": f"[对话历史摘要，仅供上下文，不是用户新问题]\n{summary}"
            }
        ]
        compressed.extend(new_messages)

        logger.info(
            f"[消息压缩] 原始{len(messages)}条 -> 压缩后{len(compressed)}条 "
            f"(保留最近{self.max_turns}轮，旧对话已摘要)"
        )
        return compressed

    def _generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        生成对话摘要（简化版）

        后续可升级为 LLM 智能摘要，当前使用截断拼接保证实时性
        """
        summary_parts = []
        pending_user = None

        for message in messages:
            role = message.get("role")
            content = message.get("content", "")
            short = content[:50] + "..." if len(content) > 50 else content

            if role == "user":
                if pending_user:
                    summary_parts.append(f"Q: {pending_user}")
                pending_user = short
            elif role == "assistant":
                if pending_user:
                    summary_parts.append(f"Q: {pending_user} A: {short}")
                    pending_user = None
                elif short.startswith("[对话历史摘要"):
                    summary_parts.append(short)

        if pending_user:
            summary_parts.append(f"Q: {pending_user}")

        return "；".join(summary_parts) if summary_parts else "历史对话内容已摘要"
