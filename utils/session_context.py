"""会话级用户上下文管理。

为什么需要这个模块？
----------------------
原项目用 random.choice() 模拟用户身份和位置，这在真实产品逻辑里是说不通的——
用户登录后，ID 和位置在会话内应当是固定的。

但 LangChain 的 @tool 函数是无状态的（由 Agent 内部调用，拿不到 Streamlit 的
session_state），所以需要一个中间层：Streamlit 前端把当前用户信息写入这里，
工具函数从这里读。

实现演进
----------------------
v1（已废弃）：用 threading.local()。问题是 LangGraph 的 ReAct Agent 内部用
ThreadPoolExecutor 跑工具调用，子线程**不会**继承父线程的 threading.local 值，
导致工具读到的永远是默认值——用户切换城市无效，IP 定位被 VPN 影响（部署后
实际暴露的 bug）。

v2（当前）：模块级简单变量。Streamlit 单进程多 session 场景下：
- 每个 user 切换 user_options 时调用 set_user_id/set_location 覆盖全局值
- 工具函数（无论在哪个线程）都读到最新值，行为可预测
- 理论上多用户并发时会有竞争，但对 demo 场景可接受（且 Streamlit 本身按 session
  rerun，竞争窗口极小）
"""
from typing import Optional

# 默认测试用户（跑评测脚本、单测时用这个，避免依赖 Web 上下文）
DEFAULT_USER_ID = "1001"
DEFAULT_LOCATION: Optional[str] = None  # None 表示走 IP 定位兜底

# 模块级状态：进程内全局共享，跨线程可见
_user_id: str = DEFAULT_USER_ID
_location: Optional[str] = DEFAULT_LOCATION


def current_user_id() -> str:
    """获取当前会话的用户 ID，默认 1001。"""
    return _user_id


def current_location() -> Optional[str]:
    """获取当前会话的用户位置，未设置返回 None（调用方兜底用 IP 定位）。"""
    return _location


def set_user_id(user_id: str) -> None:
    """前端登录后调用，绑定当前会话的用户 ID。"""
    global _user_id
    _user_id = user_id


def set_location(location: Optional[str]) -> None:
    """前端可调用，设置当前会话的用户位置（如手动切换城市）。"""
    global _location
    _location = location


def reset() -> None:
    """重置上下文（登出/测试清理时用）。"""
    global _user_id, _location
    _user_id = DEFAULT_USER_ID
    _location = DEFAULT_LOCATION
