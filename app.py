import os
from typing import Optional

import streamlit as st

from agent.react_agent import ReactAgent
from agent.tools.agent_tools import configure_rag_model
from model.factory import build_chat_model
from utils.logger_handler import logger
from utils.session_context import set_location, set_user_id
from utils.user_profile import load_user_profile, save_user_profile
from database.profile_db import UserProfile

# ============================================================
# 页面基础配置
# ============================================================
st.set_page_config(
    page_title="智扫通 · 智能客服",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

# 轻量样式：只做「留白 + 宽度 + 圆角」这类不与框架打架的微调，不堆 hack CSS。
# 设计取向参考 ChatGPT/官方 Streamlit Gallery：克制留白、单一主色、干净即可。
st.markdown(
    """
    <style>
      /* 内容居中收窄，留白更舒展（参考 ChatGPT ~768px 内容区） */
      .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 820px;
      }
      /* 聊天气泡轻圆角，去掉默认硬边感 */
      [data-testid="stChatMessage"] {
        padding: 0.6rem 0.85rem;
        border-radius: 0.75rem;
      }
      /* 侧边栏分组标题更紧凑 */
      [data-testid="stSidebar"] h2 {
        margin-top: 0.4rem;
        margin-bottom: 0.5rem;
        font-size: 1.02rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🤖 智扫通机器人智能客服")
st.caption("LangGraph ReAct Agent + RAG 检索增强　·　扫地机器人售后场景")

# ============================================================
# API Key 配置（环境变量 vs 侧边栏手填，二选一）
# ============================================================
env_dashscope_key = os.getenv("DASHSCOPE_API_KEY")
env_mimo_key = os.getenv("MIMO_API_KEY")

with st.sidebar:
    st.header("⚙️ 模型配置")

    if not env_dashscope_key and not env_mimo_key:
        with st.expander("📖 如何获取 API Key", expanded=False):
            st.markdown(
                """
                **阿里云百炼（推荐）**
                - [bailian.console.aliyun.com](https://bailian.console.aliyun.com/)
                - 新用户有免费额度

                **小米 MiMo（备选）**
                - [mimo.xiaomi.com](https://mimo.xiaomi.com/)
                - Base URL: `https://token-plan-sgp.xiaomimimo.com/v1`
                """
            )

        st.subheader("阿里云 DashScope")
        dashscope_key = st.text_input("DashScope API Key", type="password", key="dashscope_key_input")
        st.divider()
        st.subheader("小米 MiMo")
        mimo_key = st.text_input("MiMo API Key", type="password", key="mimo_key_input")
        mimo_base_url = st.text_input(
            "MiMo Base URL",
            value="https://token-plan-sgp.xiaomimimo.com/v1",
            key="mimo_base_input",
        )
        if not dashscope_key and not mimo_key:
            st.warning("⚠️ 请配置 API Key 后再开始对话")
        st.divider()
    else:
        st.success("✅ 共享 API Key 已就绪")
        if env_dashscope_key:
            st.caption("模型：阿里云百炼 Qwen-Plus")
        elif env_mimo_key:
            st.caption("模型：小米 MiMo")
        st.caption("💡 共享额度有限，请合理使用")
        dashscope_key = env_dashscope_key
        mimo_key = env_mimo_key
        mimo_base_url = os.getenv("MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1")
        st.divider()


# ============================================================
# 会话级模型构建（按签名缓存，配置变更自动重建）
# ============================================================
def resolve_chat_config() -> tuple[dict, str]:
    """从侧边栏/环境变量解析当前应使用的 chat 模型配置。"""
    if mimo_key:
        kwargs = {
            "provider": "mimo",
            "api_key": mimo_key,
            "base_url": mimo_base_url,
            "model_name": os.getenv("MIMO_CHAT_MODEL"),
        }
        sig = f"mimo:{mimo_key}:{mimo_base_url}"
    elif dashscope_key:
        # DashScope 的 ChatTongyi 隐式从 os.environ 读取 API Key（不支持构造时显式传参），
        # 因此需要在调用 build_chat_model() 之前将 key 写入进程环境变量。
        # 这在 Streamlit 单进程场景下是安全的：只影响当前进程，不会泄漏给其他用户。
        # 面试/演示场景依赖此机制实现"开箱即用"（.env 或共享 Key），勿移除。
        os.environ["DASHSCOPE_API_KEY"] = dashscope_key
        kwargs = {"provider": "dashscope"}
        sig = f"dashscope:{dashscope_key}"
    else:
        kwargs = {}
        sig = "default"
    return kwargs, sig


@st.cache_resource(show_spinner="📚 首次启动正在初始化知识库（约 30-60 秒）...")
def _ensure_knowledge_base_loaded() -> bool:
    """首次部署时自动把 data/ 下的文档加载进 Chroma。

    chroma_db/ 被 .gitignore，Streamlit Cloud 部署后向量库是空的。
    @st.cache_resource 保证整个 server 进程只跑一次，依赖 MD5 去重幂等。
    """
    from rag.vector_store import VectorStoreService

    VectorStoreService().load_document()
    return True


# ============================================================
# 预填用户档案（首次启动自动写入 SQLite，@st.cache_resource 保证只跑一次）
# ============================================================
DEFAULT_PROFILES = {
    "1001": UserProfile(user_id="1001", age=35, address="深圳南山区科技园", home_area=80.0,
                        has_pets=True, has_carpets=True, device_model="小米扫地机器人2S"),
    "1002": UserProfile(user_id="1002", age=28, address="合肥蜀山区", home_area=65.0,
                        has_pets=False, has_carpets=False, device_model="石头P10"),
    "1003": UserProfile(user_id="1003", age=45, address="杭州西湖区", home_area=120.0,
                        has_pets=True, has_carpets=True, device_model="科沃斯X2"),
    "1004": UserProfile(user_id="1004", age=60, address="北京朝阳区", home_area=90.0,
                        has_pets=False, has_carpets=False, device_model="追觅S20"),
    "1005": UserProfile(user_id="1005", age=32, address="成都高新区", home_area=100.0,
                        has_pets=True, has_carpets=True, device_model="云鲸J3"),
}


@st.cache_resource(show_spinner=False)
def _init_default_profiles() -> bool:
    """预填测试用户档案到 SQLite，进程级只跑一次。"""
    from database.profile_db import ProfileDatabase
    db = ProfileDatabase()
    for uid, profile in DEFAULT_PROFILES.items():
        if db.get_profile(uid) is None:
            db.save_profile(profile)
    return True


# ============================================================
# 赵先生（1005）预置对话历史：8 轮，用于演示 L3 消息压缩
# ============================================================
PREBUILT_HISTORY_1005 = [
    {
        "role": "user",
        "content": "扫地机器人回充失败，指示灯一直在闪，怎么排查？"
    },
    {
        "role": "assistant",
        "content": "请按以下步骤排查：\n\n1. **检查充电座是否通电** — 确认电源插头插紧，适配器指示灯亮起\n2. **清洁充电触点** — 用干布擦拭机器人底部和充电座的金属触点，去除氧化层\n3. **清理充电座周围** — 充电座前方 3 米、左右 1 米内不要有障碍物\n4. **检查回充传感器** — 机器人前方的红外传感器是否有灰尘遮挡\n5. **手动回充测试** — 将机器人手动推到充电座上，看能否正常充电\n\n如果以上都无效，可能是电池或主板故障，建议联系售后。\n\n📚 参考来源：故障排除.txt"
    },
    {
        "role": "user",
        "content": "充电触点氧化了怎么办？用什么擦？"
    },
    {
        "role": "assistant",
        "content": "充电触点氧化处理方法：\n\n1. **用干布或橡皮擦** — 轻轻擦拭金属触点表面，去除氧化层\n2. **酒精棉片** — 如果氧化较严重，可用 75% 酒精棉片擦拭，晾干后再使用\n3. **不要用砂纸** — 会损坏镀层，导致更快氧化\n4. **定期保养** — 建议每月检查一次充电触点，保持干燥清洁\n\n⚠️ 注意：擦拭前请断开充电座电源，避免短路。\n\n📚 参考来源：故障排除.txt、扫地机器人100问2.txt"
    },
    {
        "role": "user",
        "content": "成都今天天气适合拖地吗？"
    },
    {
        "role": "assistant",
        "content": "让我查询一下成都的实时天气...\n\n成都市当前天气：气温 24°C，空气湿度 65%，降水量 0mm，风速 8km/h。\n\n**适合拖地** ✅ — 湿度适中，无降水，拖地后地面能较快干燥。建议：\n- 出水量设为中档\n- 拖完后开窗通风 15 分钟\n- 木地板区域建议低水量"
    },
    {
        "role": "user",
        "content": "HEPA 滤网多久需要更换一次？"
    },
    {
        "role": "assistant",
        "content": "HEPA 滤网更换周期取决于使用频率和环境：\n\n| 场景 | 建议更换周期 |\n|------|-------------|\n| 普通家庭 | 每 3-6 个月 |\n| 有宠物 | 每 2-3 个月 |\n| 灰尘较大 | 每 2 个月 |\n\n**判断是否需要更换的信号：**\n- 滤网颜色明显变黑\n- 吸力明显下降\n- 清洗后仍无法恢复\n\n**保养建议：**\n- 每 1-2 周取出轻轻拍打除尘\n- 可水洗的滤网每月水洗一次，完全晾干后再装回\n- 建议备一个替换滤网轮换使用\n\n📚 参考来源：扫拖一体机器人100问.txt、选购指南.txt"
    },
    {
        "role": "user",
        "content": "帮我生成本月使用报告"
    },
    {
        "role": "assistant",
        "content": "## 📊 赵先生 2026-06 扫地机器人使用报告\n\n### 基本信息\n- **用户**：赵先生（成都）\n- **设备**：云鲸 J3\n- **家庭面积**：100㎡（有猫、有地毯）\n\n### 清洁效率\n- **覆盖率**：82%\n- **日均清扫面积**：45㎡\n- **清扫效率**：78%\n- **定时任务使用**：22 次/月\n\n### 耗材状态\n- **主刷寿命**：剩余 252 天\n- **HEPA 滤网**：剩余 44% ⚠️ 建议近期更换\n- **尘盒清理频率**：每 2 天\n\n### 对比分析\n- 清洁效率优于 72% 同面积用户\n- 有宠物家庭中表现优秀\n\n### 💡 保养建议\n1. **滤网需要更换** — 剩余 44%，建议本月内更换新滤网\n2. **地毯区域** — 建议开启地毯增压模式，提升覆盖率\n3. **宠物毛发** — 每周清理主刷缠绕的毛发，保持吸力\n4. **拖布** — 有宠物家庭建议每 2 个月更换拖布"
    },
    {
        "role": "user",
        "content": "有猫的话，主刷怎么清理毛发缠绕？"
    },
    {
        "role": "assistant",
        "content": "有猫家庭主刷毛发清理方法：\n\n### 日常清理（建议每周 1 次）\n1. **取出主刷** — 按下主刷卡扣，取出滚刷\n2. **用清理工具割断毛发** — 随机附带的清理刀片沿滚刷槽割断缠绕毛发\n3. **手动拉出毛发** — 从两端向中间拉出\n4. **清理轴承** — 主刷两端的轴承处容易积聚毛发，用牙签挑出\n\n### 减少缠绕的技巧\n- **选择防缠绕主刷** — 硅胶条设计的主刷不容易缠绕长毛\n- **提高清扫频率** — 每天清扫比每周清扫毛发堆积少，缠绕更轻\n- **先扫后拖模式** — 先用吸力模式清理毛发，再拖地\n\n### ⚠️ 注意\n- 不要用剪刀直接剪，容易损伤主刷\n- 如果缠绕严重导致主刷不转，可能是电机保护，清理后重启即可\n\n📚 参考来源：故障排除.txt、扫拖一体机器人100问.txt"
    },
    {
        "role": "user",
        "content": "边刷磨损了需要更换吗？"
    },
    {
        "role": "assistant",
        "content": "边刷磨损到以下程度建议更换：\n\n### 更换信号\n- **明显变短** — 边刷长度不足原来的 1/2\n- **变形弯曲** — 无法贴合地面，清扫边角有死角\n- **松动脱落** — 转轴磨损导致边刷固定不稳\n\n### 更换周期\n| 使用场景 | 建议更换周期 |\n|---------|-------------|\n| 普通家庭 | 每 3-6 个月 |\n| 有宠物/毛发多 | 每 2-3 个月 |\n\n### 建议\n- 赵先生家有猫，建议每 3 个月检查一次边刷状态\n- 可在官方商城购买原装边刷，兼容性更好\n- 更换时注意左右边刷方向不同，不要装反\n\n📚 参考来源：扫地机器人100问2.txt、故障排除.txt"
    },
]


def get_or_build_agent() -> ReactAgent | None:
    kwargs, sig = resolve_chat_config()
    if sig == "default":
        return None

    cached_sig = st.session_state.get("agent_config_sig")
    if "agent" in st.session_state and cached_sig == sig:
        return st.session_state["agent"]

    try:
        chat_model = build_chat_model(**kwargs)
        configure_rag_model(chat_model)
        _ensure_knowledge_base_loaded()
        st.session_state["agent"] = ReactAgent(chat_model=chat_model)
        st.session_state["agent_config_sig"] = sig
        logger.info(f"[app]重建 Agent，配置签名={sig}")
        return st.session_state["agent"]
    except ValueError as e:
        st.error(f"模型配置错误：{e}")
        return None


# ============================================================
# 侧边栏：会话级用户上下文 + 用户切换清空对话
# ============================================================
USER_OPTIONS = {
    "1001 - 张先生（深圳）": ("1001", "深圳"),
    "1002 - 李女士（合肥）": ("1002", "合肥"),
    "1003 - 王先生（杭州）": ("1003", "杭州"),
    "1004 - 陈女士（北京）": ("1004", "北京"),
    "1005 - 赵先生（成都）": ("1005", "成都"),
}

with st.sidebar:
    # 预填用户档案（首次启动自动写入 SQLite）
    _init_default_profiles()

    st.header("👤 测试用户")
    selected = st.selectbox("当前登录用户", list(USER_OPTIONS.keys()), key="user_select")
    uid, loc = USER_OPTIONS[selected]
    set_user_id(uid)
    set_location(loc)
    st.caption(f"用户 ID `{uid}`　·　位置 `{loc}`")

    # 切换用户时加载对话历史（赵先生有预置历史，其他用户清空）
    if st.session_state.get("active_user") != selected:
        st.session_state["active_user"] = selected
        if uid == "1005":
            st.session_state["messages"] = list(PREBUILT_HISTORY_1005)
        else:
            st.session_state["messages"] = []
        # 加载用户档案
        load_user_profile(uid)

    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

    # 用户档案表单
    with st.expander("📝 用户档案（可选）", expanded=False):
        st.caption("填写后可获得个性化推荐")

        # 获取当前档案（如果有）
        from utils.user_profile import current_profile
        profile = current_profile() or UserProfile(user_id=uid)

        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input(
                "年龄",
                min_value=1, max_value=120,
                value=profile.age or 30,
                key="profile_age"
            )
            has_pets = st.checkbox(
                "是否有宠物",
                value=profile.has_pets if profile.has_pets is not None else False,
                key="profile_pets"
            )
        with col2:
            home_area = st.number_input(
                "家庭面积（㎡）",
                min_value=10.0, max_value=500.0,
                value=profile.home_area or 80.0,
                key="profile_area"
            )
            has_carpets = st.checkbox(
                "是否有地毯",
                value=profile.has_carpets if profile.has_carpets is not None else False,
                key="profile_carpets"
            )

        address = st.text_input(
            "详细地址",
            value=profile.address or "",
            key="profile_address",
            placeholder="例如：深圳市南山区科技园"
        )
        device_model = st.text_input(
            "设备型号",
            value=profile.device_model or "",
            key="profile_device",
            placeholder="例如：小米扫地机器人 2S"
        )

        if st.button("💾 保存档案", use_container_width=True):
            new_profile = UserProfile(
                user_id=uid,
                age=age,
                address=address if address else None,
                home_area=home_area,
                has_pets=has_pets,
                has_carpets=has_carpets,
                device_model=device_model if device_model else None
            )
            if save_user_profile(new_profile):
                load_user_profile(uid)  # 重新加载到会话
                st.success("✅ 档案已保存")
                st.rerun()
            else:
                st.error("❌ 保存失败，请重试")

    # ============================================================
    # 记忆状态展示区
    # ============================================================
    with st.expander("🧠 记忆状态", expanded=True):
        # L2 用户档案状态
        from utils.user_profile import current_profile as _get_profile
        _profile = _get_profile()
        if _profile:
            st.markdown("**📝 用户档案**")
            _parts = []
            if _profile.age:
                _parts.append(f"年龄 {_profile.age}岁")
            if _profile.address:
                _parts.append(_profile.address)
            if _profile.home_area:
                _parts.append(f"{_profile.home_area:.0f}㎡")
            if _profile.has_pets is not None:
                _parts.append("有宠物" if _profile.has_pets else "无宠物")
            if _profile.has_carpets is not None:
                _parts.append("有地毯" if _profile.has_carpets else "无地毯")
            if _profile.device_model:
                _parts.append(_profile.device_model)
            st.caption(" · ".join(_parts))
        else:
            st.markdown("**📝 用户档案**")
            st.caption("未填写 — 侧边栏可填写以获取个性化推荐")

        # L3 对话压缩状态
        st.markdown("**💬 对话记忆**")
        _messages = st.session_state.get("messages", [])
        _user_turns = sum(1 for m in _messages if m.get("role") == "user")
        _max_turns = 6  # 压缩阈值
        if _user_turns > _max_turns:
            st.caption(f"对话轮数：{_user_turns} 轮　·　⚠️ 已触发压缩（保留最近 {_max_turns} 轮）")
        else:
            st.caption(f"对话轮数：{_user_turns} 轮　·　压缩阈值：{_max_turns} 轮")

    st.divider()
    st.markdown("**💡 试试这些问题：**")
    EXAMPLE_QUESTIONS = [
        ("🔧", "扫地机器人无法正常回充，该怎么排查？"),
        ("🧹", "家里有宠物，应该怎么维护主刷和滤网？"),
        ("🌤️", "我所在城市的天气适合拖地吗？"),
        ("📊", "帮我生成本月使用报告，并给出保养建议。"),
    ]
    for icon, q in EXAMPLE_QUESTIONS:
        if st.button(f"{icon}　{q}", key=f"q_{q[:6]}", use_container_width=True):
            st.session_state["pending_prompt"] = q
            st.rerun()


# ============================================================
# 主聊天区
# ============================================================
agent = get_or_build_agent()

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 欢迎语：仅首屏（无历史消息时）展示
if not st.session_state["messages"]:
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(
            f"""你好，我是 **智扫通智能客服**。我可以帮你：

- 🔧 **故障排查** —— 回充失败、拖地不干净、噪音异常等
- 🧹 **维护保养** —— 滤网/边刷/主刷的清理与更换周期
- 🛒 **选购建议** —— 户型、宠物、地毯等场景适配
- 📊 **使用报告** —— 基于使用记录生成月度报告与保养建议

> 当前登录身份：**{selected}**，切换用户会自动开新对话。"""
        )

# 历史消息回放
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🧑"):
        st.markdown(msg["content"])

# 输入与流式响应
# 支持两种输入：chat_input 直接打字，或侧边栏示例问题按钮（pending_prompt）
prompt = st.chat_input("输入你的问题，例如：扫地机器人无法回充怎么办？")
if not prompt and st.session_state.get("pending_prompt"):
    prompt = st.session_state["pending_prompt"]
    st.session_state["pending_prompt"] = None  # 消费掉，避免回放

if prompt:
    if agent is None:
        st.error("⚠️ 请先在侧边栏配置 API Key")
    else:
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)
        st.session_state["messages"].append({"role": "user", "content": prompt})

        with st.chat_message("assistant", avatar="🤖"):
            # st.status 容器：实时展示 Agent 推理过程（思考/工具调用/工具返回），
            # 收到最终回答后自动收起，只把答案留在 chat 区。像真 Agent 的实时推理流。
            status = st.status("🤔 正在思考...", expanded=True)
            answer_placeholder = st.empty()

            answer_text = ""
            step_idx = 0
            status_finalized = False

            for kind, content in agent.execute_stream(prompt, st.session_state.get("messages", [])):
                if kind == "answer":
                    # 收到第一个回答字符：收起推理过程，开始逐字输出答案
                    if not status_finalized:
                        status.update(label="✅ 推理完成", state="complete", expanded=False)
                        status_finalized = True
                    answer_text += content
                    answer_placeholder.markdown(answer_text)
                else:
                    step_idx += 1
                    if kind == "thought":
                        status.update(label=f"💭 正在分析（第 {step_idx} 步）...")
                        status.markdown(f"**💭 思考**：{content}")
                    elif kind == "tool_call":
                        status.update(label=f"🔧 正在调用工具（第 {step_idx} 步）...")
                        status.markdown(content)
                    elif kind == "tool_result":
                        status.update(label=f"📥 获取到信息（第 {step_idx} 步）...")
                        status.markdown(content)

            # 兜底：Agent 没产出最终回答
            if not answer_text:
                answer_text = "⚠️ 未能生成有效回答，请重试或换一种问法。"
                answer_placeholder.markdown(answer_text)
                status.update(label="⚠️ 未能生成有效回答", state="error", expanded=False)
            elif not status_finalized:
                # 有内容但未走 answer 分支（理论上不会，保险处理）
                status.update(label="✅ 推理完成", state="complete", expanded=False)

        st.session_state["messages"].append({"role": "assistant", "content": answer_text})
