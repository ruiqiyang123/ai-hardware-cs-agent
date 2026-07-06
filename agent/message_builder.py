from typing import Dict, List, Optional


def build_agent_messages(query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    """Build agent input messages without duplicating the active user turn."""
    messages = list(chat_history or [])
    if messages and messages[-1].get("role") == "user" and messages[-1].get("content") == query:
        return messages
    messages.append({"role": "user", "content": query})
    return messages
