def should_short_circuit_rag_answer(tool_name: str, tool_output: str) -> bool:
    """Return True when a RAG tool result is good enough to show as the answer."""
    output = (tool_output or "").strip()
    return tool_name == "rag_summarize" and bool(output) and not output.startswith("Error:")
