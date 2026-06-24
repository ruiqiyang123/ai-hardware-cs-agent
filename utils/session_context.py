"""会话级用户上下文管理。

为什么需要这个模块？
----------------------
原项目用 random.choice() 模拟用户身份和位置，这在真实产品逻辑里是说不通的——
用户登录后，ID 和位置在会话内应当是固定的。

但 LangChain 的 @tool 函数是无状态的（由 Agent 内部调用，拿不到 Streamlit 的
session_state），所以需要一个中间层：Streamlit 前端把当前用户信息写入这里，
工具函数从这里读。

实现方式采用「线程局部变量 + 默认值」，既能在 Streamlit 多会话场景下工作，
也能在非 Web 环境（如评测脚本、单测）下用默认值跑通。
"""
import threading
from typing import Optional

# 线程局部存储：每个请求线程（Streamlit 会话）有自己独立的上下文
_local = threading.local()

# 默认测试用户（跑评测脚本、单测时用这个，避免依赖 Web 上下文）
DEFAULT_USER_ID = "1001"
DEFAULT_LOCATION: Optional[str] = None  # None 表示走 IP 定位兜底


def current_user_id() -> str:
    """获取当前会话的用户 ID，默认 1001。"""
    return getattr(_local, "user_id", DEFAULT_USER_ID)


def current_location() -> Optional[str]:
    """获取当前会话的用户位置，未设置返回 None（调用方兜底用 IP 定位）。"""
    return getattr(_local, "location", DEFAULT_LOCATION)


def set_user_id(user_id: str) -> None:
    """前端登录后调用，绑定当前会话的用户 ID。"""
    _local.user_id = user_id


def set_location(location: Optional[str]) -> None:
    """前端可调用，设置当前会话的用户位置（如手动切换城市）。"""
    _local.location = location


def reset() -> None:
    """重置当前线程的上下文（登出/测试清理时用）。"""
    _local.user_id = DEFAULT_USER_ID
    _local.location = DEFAULT_LOCATION
