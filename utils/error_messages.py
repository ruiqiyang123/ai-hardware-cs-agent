"""用户可读错误提示。

外部模型服务报错时，Streamlit Cloud 会展示红色 traceback。这里把底层异常
映射成安全、可操作的文案：不暴露 API Key、请求细节或完整异常堆栈。
"""


def format_agent_error(error: Exception) -> str:
    """把 Agent/模型异常转换成适合展示给用户的提示。"""
    raw = str(error).lower()

    if any(token in raw for token in ["invalid api", "api-key", "apikey", "unauthorized", "forbidden"]):
        return (
            "⚠️ 模型服务暂时不可用：当前 API Key 可能无效或权限不足。\n\n"
            "请稍后重试；如果连续失败，请联系项目作者检查后台 MiMo 配置。"
        )

    if any(token in raw for token in ["quota", "rate limit", "throttl", "insufficient", "余额", "限流"]):
        return (
            "⚠️ 模型服务暂时不可用：共享额度可能不足或触发限流。\n\n"
            "请稍后重试；如果连续失败，请联系项目作者检查后台 MiMo 额度。"
        )

    return (
        "⚠️ 模型服务暂时不可用，未能生成有效回答。\n\n"
        "请稍后重试；如果连续失败，请联系项目作者检查后台 MiMo 服务。"
    )
