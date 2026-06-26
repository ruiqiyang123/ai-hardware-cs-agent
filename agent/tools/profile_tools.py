"""
用户档案相关工具：让 Agent 能访问用户档案信息

通过 get_user_profile 工具，Agent 可以获取用户的年龄、地址、家庭面积、
是否有宠物、是否有地毯、设备型号等信息，用于个性化推荐。
"""

from langchain_core.tools import tool
from utils.user_profile import current_profile
from utils.logger_handler import logger


@tool(description="获取当前用户的档案信息（年龄、地址、家庭面积、是否有宠物、是否有地毯、设备型号），返回结构化字符串")
def get_user_profile() -> str:
    """获取当前用户档案，用于个性化推荐

    当用户询问适合自己家庭的情况、需要个性化建议时，调用此工具获取用户档案。

    Returns:
        用户档案的结构化描述，如"年龄：35岁；地址：深圳南山区；家庭面积：120平方米；是否有宠物：是；是否有地毯：否；设备型号：小米扫地机器人2S"
        如果用户未填写档案，返回"当前用户未填写档案信息"
    """
    profile = current_profile()

    if not profile:
        return "当前用户未填写档案信息，无法提供个性化建议"

    parts = []
    if profile.age:
        parts.append(f"年龄：{profile.age}岁")
    if profile.address:
        parts.append(f"地址：{profile.address}")
    if profile.home_area:
        parts.append(f"家庭面积：{profile.home_area}平方米")
    if profile.has_pets is not None:
        parts.append(f"是否有宠物：{'是' if profile.has_pets else '否'}")
    if profile.has_carpets is not None:
        parts.append(f"是否有地毯：{'是' if profile.has_carpets else '否'}")
    if profile.device_model:
        parts.append(f"设备型号：{profile.device_model}")

    profile_str = "；".join(parts) if parts else "用户档案未填写详细信息"
    logger.info(f"[get_user_profile] 获取到档案: {profile_str}")
    return profile_str
