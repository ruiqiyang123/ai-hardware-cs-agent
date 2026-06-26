"""
用户档案会话管理

遵循 session_context.py 的模式，使用模块级全局变量存储当前会话的用户档案，
供工具函数访问（工具函数无法直接访问 Streamlit 的 session_state）。
"""

from typing import Optional
from database.profile_db import ProfileDatabase, UserProfile
from utils.logger_handler import logger


# 模块级状态：进程内全局共享（类似 session_context.py 的设计）
_profile_db = ProfileDatabase()
_current_profile: Optional[UserProfile] = None


def current_profile() -> Optional[UserProfile]:
    """获取当前会话的用户档案

    供工具函数调用，返回当前用户填写的档案信息
    """
    global _current_profile
    return _current_profile


def load_user_profile(user_id: str) -> Optional[UserProfile]:
    """从数据库加载用户档案到会话

    Args:
        user_id: 用户 ID

    Returns:
        用户档案对象，不存在则返回 None
    """
    global _current_profile
    profile = _profile_db.get_profile(user_id)
    _current_profile = profile
    if profile:
        logger.info(f"[user_profile] 已加载用户档案: {user_id}")
    else:
        logger.info(f"[user_profile] 用户 {user_id} 暂无档案")
    return profile


def save_user_profile(profile: UserProfile) -> bool:
    """保存用户档案到数据库

    Args:
        profile: 用户档案对象

    Returns:
        是否保存成功
    """
    global _current_profile
    success = _profile_db.save_profile(profile)
    if success:
        _current_profile = profile  # 保存后更新会话状态
    return success


def reset_profile() -> None:
    """重置当前档案（用户切换或测试清理时用）"""
    global _current_profile
    _current_profile = None
