import os
from typing import Optional

import streamlit as st

from agent.react_agent import ReactAgent
from agent.tools.agent_tools import configure_rag_model
from database.profile_db import ProfileDatabase, UserProfile
from model.factory import build_chat_model
from utils.error_messages import format_agent_error
from utils.logger_handler import logger
from utils.model_config import DEFAULT_MIMO_BASE_URL, DEFAULT_MIMO_CHAT_MODEL, build_chat_config
from utils.session_context import set_location, set_user_id
from utils.user_profile import load_user_profile, save_user_profile


st.set_page_config(
    page_title="KeyGuard · 硬件钱包客服",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 820px;
      }
      [data-testid="stChatMessage"] {
        padding: 0.6rem 0.85rem;
        border-radius: 0.75rem;
      }
      [data-testid="stSidebar"] h2 {
        margin-top: 0.4rem;
        margin-bottom: 0.5rem;
        font-size: 1.02rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔐 KeyGuard 硬件钱包智能客服")
st.caption("LangGraph ReAct Agent + RAG 检索增强 · 硬件钱包售后与安全自助服务")


def _runtime_secret(name: str) -> Optional[str]:
    """读取环境变量 / Streamlit Secrets，避免 Cloud 与本地配置方式不一致。"""
    value = os.getenv(name)
    if value:
        return value

    try:
        secret_value = st.secrets.get(name)
    except Exception:
        return None
    return str(secret_value) if secret_value else None


env_mimo_key = _runtime_secret("MIMO_API_KEY")
env_mimo_base_url = _runtime_secret("MIMO_BASE_URL") or DEFAULT_MIMO_BASE_URL
env_mimo_model = _runtime_secret("MIMO_CHAT_MODEL") or DEFAULT_MIMO_CHAT_MODEL
selected_provider = "mimo"
dashscope_key = None
mimo_key = env_mimo_key
mimo_base_url = env_mimo_base_url
mimo_model_name = env_mimo_model

with st.sidebar:
    st.caption(f"模型：MiMo · `{mimo_model_name}`")
    st.divider()


def resolve_chat_config() -> tuple[dict, str]:
    """从环境变量解析当前应使用的 chat 模型配置。"""
    config = build_chat_config(
        provider=selected_provider,
        dashscope_key=dashscope_key,
        mimo_key=mimo_key,
        mimo_base_url=mimo_base_url,
        mimo_model_name=mimo_model_name,
    )
    return config.kwargs, config.signature


@st.cache_resource(show_spinner="📚 首次启动正在初始化硬件钱包知识库（约 30-60 秒）...")
def _ensure_knowledge_base_loaded() -> bool:
    """首次部署时自动把 data/ 下的文档加载进 Chroma。"""
    from rag.vector_store import VectorStoreService

    VectorStoreService().load_document()
    return True


DEFAULT_PROFILES = {
    "1001": UserProfile(
        user_id="1001",
        experience_level="新手",
        region="深圳",
        device_model="KeyGuard Mini",
        preferred_chains="BTC, ETH",
        connection_method="USB-C",
        passphrase_enabled=False,
        backup_verified=True,
    ),
    "1002": UserProfile(
        user_id="1002",
        experience_level="进阶",
        region="上海",
        device_model="KeyGuard Pro",
        preferred_chains="ETH, Polygon, Arbitrum",
        connection_method="蓝牙",
        passphrase_enabled=True,
        backup_verified=True,
    ),
    "1003": UserProfile(
        user_id="1003",
        experience_level="新手",
        region="杭州",
        device_model="KeyGuard Mini",
        preferred_chains="USDT-TRC20, ETH",
        connection_method="USB-C",
        passphrase_enabled=False,
        backup_verified=False,
    ),
    "1004": UserProfile(
        user_id="1004",
        experience_level="资深",
        region="北京",
        device_model="KeyGuard Max",
        preferred_chains="BTC, ETH, SOL",
        connection_method="USB-C",
        passphrase_enabled=True,
        backup_verified=True,
    ),
    "1005": UserProfile(
        user_id="1005",
        experience_level="进阶",
        region="成都",
        device_model="KeyGuard Pro",
        preferred_chains="ETH, BTC, SOL",
        connection_method="蓝牙",
        passphrase_enabled=True,
        backup_verified=True,
    ),
}


@st.cache_resource(show_spinner=False)
def _init_default_profiles() -> bool:
    """预填测试用户档案到 SQLite，进程级只跑一次。"""
    from database.profile_db import ProfileDatabase

    db = ProfileDatabase()
    for uid, profile in DEFAULT_PROFILES.items():
        existing = db.get_profile(uid)
        if existing is None:
            db.save_profile(profile)
    return True


PREBUILT_HISTORY_1005 = [
    {
        "role": "user",
        "content": "KeyGuard Pro 蓝牙连接不上手机，App 一直显示未发现设备，怎么排查？",
    },
    {
        "role": "assistant",
        "content": "可以按这个顺序排查：\n\n1. **确认设备已解锁并停留在主页**，锁屏状态下 App 可能无法完成配对。\n2. **删除旧配对记录**，在手机系统蓝牙设置和 KeyGuard App 内都移除旧设备后重新配对。\n3. **检查系统权限**，确认 App 已获得蓝牙和附近设备权限。\n4. **升级 App 与固件**，旧版本可能存在连接兼容问题。\n5. **改用 USB-C 交叉验证**，如果 USB-C 正常，问题更可能在蓝牙模块或手机权限。\n\n安全提醒：连接排查过程中不要在手机或网页里输入助记词、私钥或 PIN。\n\n📚 参考来源：故障排除.txt、安全使用指南.txt",
    },
    {
        "role": "user",
        "content": "如果我怀疑助记词被别人看到了，还能继续用这个钱包吗？",
    },
    {
        "role": "assistant",
        "content": "不建议继续使用这组助记词。助记词疑似泄露时，要按资产已经暴露来处理：\n\n1. **立即创建新钱包**，在安全环境中生成新的助记词并完成离线备份。\n2. **把旧钱包资产转移到新地址**，优先转移价值较高和流动性高的资产。\n3. **撤销旧钱包授权**，检查 DeFi、NFT 市场和跨链桥的长期授权。\n4. **废弃旧助记词**，不要再接收新资产到旧地址。\n\n客服不会、也不能要求你提供助记词、私钥或 PIN。\n\n📚 参考来源：助记词与备份.txt、安全使用指南.txt",
    },
    {
        "role": "user",
        "content": "设备今天突然开不了机，屏幕完全不亮，是不是硬件坏了？",
    },
    {
        "role": "assistant",
        "content": "先不要判断为设备损坏，可以按“供电、线缆、端口、设备状态”逐步排查：\n\n1. **换一根支持数据传输的 USB-C 线**，不要只用充电线。\n2. **换电脑 USB 端口或 USB 电源**，优先直连，不经过扩展坞。\n3. **保持连接一段时间后再长按电源键**，排除长期未使用导致的低电量。\n4. **观察是否只有某根线或某个端口无法唤醒**，如果是，优先判断为线缆或供电问题。\n5. **多线、多端口、多电源都无响应**，再记录型号和现象进入售后检测。\n\n安全提醒：不要拆机、加热、电池改装，也不要安装第三方“维修工具”。\n\n📚 参考来源：故障排除.txt",
    },
    {
        "role": "user",
        "content": "如果 USB-C 连接后反复断开重连，要怎么判断问题在哪？",
    },
    {
        "role": "assistant",
        "content": "可以用交叉验证把问题缩小：\n\n1. **先换高质量数据线**，很多硬件钱包亮屏但无法稳定传输，是因为线只适合充电或接触不稳。\n2. **直连电脑 USB 端口**，暂时不要用 USB Hub、扩展坞和过长延长线。\n3. **换另一台电脑测试**，如果只在一台电脑断连，重点排查系统权限、驱动、杀毒软件或 USB 端口。\n4. **检查设备 USB-C 接口是否松动或有异物**，不要用尖锐金属工具清理。\n5. **记录 App 版本、系统版本、设备型号和断连时机**，多设备复现时再进入售后检测。\n\n📚 参考来源：故障排除.txt",
    },
    {
        "role": "user",
        "content": "固件升级前要注意什么？",
    },
    {
        "role": "assistant",
        "content": "固件升级前建议先做这几件事：\n\n1. **确认助记词已完成离线备份和恢复验证**。\n2. **只使用官方 App 或官网入口升级**，不要安装第三方工具提供的固件。\n3. **保证连接稳定**，USB-C 用户建议使用原装数据线，蓝牙用户保持设备电量充足。\n4. **升级前暂停交易操作**，避免升级和签名同时进行。\n5. **升级后做小额验证**，确认地址、签名和常用链账户正常。\n\n安全边界：固件升级不需要输入助记词，任何要求你输入助记词的升级页面都应视为风险。\n\n📚 参考来源：固件升级.txt、安全使用指南.txt",
    },
    {
        "role": "user",
        "content": "帮我生成本月安全使用报告。",
    },
    {
        "role": "assistant",
        "content": "## 📊 赵先生 2026-06 硬件钱包安全使用报告\n\n### 基本信息\n- **用户**：赵先生（成都）\n- **设备**：KeyGuard Pro\n- **常用链**：ETH, BTC, SOL\n- **连接方式**：蓝牙\n\n### 使用概况\n- **签名次数**：26 次/月\n- **主要操作**：ETH 转账、SOL 收款、DeFi 授权确认\n- **失败交易**：1 笔，疑似 Gas 设置偏低\n\n### 安全状态\n- **固件状态**：已是最新版\n- **助记词备份**：已完成验证\n- **Passphrase**：已开启\n- **高风险授权**：发现 1 个长期授权，建议复核\n\n### 建议\n1. 保持固件和 App 同步更新。\n2. 每月复查一次 DeFi 授权，撤销不用的授权。\n3. 大额转账继续坚持先小额测试。\n4. 蓝牙连接异常时优先使用 USB-C 做交叉验证。",
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
        st.error(f"模型服务配置错误：{e}")
        return None


USER_OPTIONS = {
    "1001 - 张先生（深圳）": ("1001", "深圳"),
    "1002 - 李女士（上海）": ("1002", "上海"),
    "1003 - 王女士（杭州）": ("1003", "杭州"),
    "1004 - 陈先生（北京）": ("1004", "北京"),
    "1005 - 赵先生（成都） · 展示记忆功能": ("1005", "成都"),
}
MEMORY_DEMO_USER_ID = "1005"
MEMORY_DEMO_SUMMARY = """赵先生此前咨询过蓝牙连接失败、助记词疑似泄露、设备开不了机、USB-C 断连、固件升级前检查和月度安全报告。

当前记忆要点：
- 设备：KeyGuard Pro，常用蓝牙连接，连接异常时可用 USB-C 交叉验证。
- 安全：Passphrase 已开启，备份已验证，需要定期复核高风险授权。
- 这段摘要只用于解释记忆机制，不会作为聊天回答展示。"""

EXPERIENCE_LEVELS = ["新手", "进阶", "资深"]
CONNECTION_METHODS = ["USB-C", "蓝牙", "USB-C + 蓝牙"]

with st.sidebar:
    _init_default_profiles()

    st.header("👤 测试用户")
    selected = st.selectbox("当前登录用户", list(USER_OPTIONS.keys()), key="user_select")
    uid, loc = USER_OPTIONS[selected]
    set_user_id(uid)
    set_location(loc)
    st.caption(f"用户 ID `{uid}` · 地区 `{loc}`")
    if uid == MEMORY_DEMO_USER_ID:
        st.info("展示记忆功能：已预置 6 轮历史对话，继续提问会触发对话压缩。", icon="🧠")

    if st.session_state.get("active_user") != selected:
        st.session_state["active_user"] = selected
        st.session_state["messages"] = list(PREBUILT_HISTORY_1005) if uid == MEMORY_DEMO_USER_ID else []
        load_user_profile(uid)

    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

    with st.expander("📝 用户档案（可选）", expanded=False):
        st.caption("填写后可获得个性化安全建议")

        from utils.user_profile import current_profile

        profile = current_profile() or UserProfile(user_id=uid)

        col1, col2 = st.columns(2)
        with col1:
            experience_default = (
                EXPERIENCE_LEVELS.index(profile.experience_level)
                if profile.experience_level in EXPERIENCE_LEVELS
                else 1
            )
            experience_level = st.selectbox(
                "使用经验",
                EXPERIENCE_LEVELS,
                index=experience_default,
                key="profile_experience_level",
            )
            passphrase_enabled = st.checkbox(
                "已开启 Passphrase",
                value=profile.passphrase_enabled if profile.passphrase_enabled is not None else False,
                key="profile_passphrase_enabled",
            )
        with col2:
            connection_default = (
                CONNECTION_METHODS.index(profile.connection_method)
                if profile.connection_method in CONNECTION_METHODS
                else 0
            )
            connection_method = st.selectbox(
                "常用连接方式",
                CONNECTION_METHODS,
                index=connection_default,
                key="profile_connection_method",
            )
            backup_verified = st.checkbox(
                "已完成备份验证",
                value=profile.backup_verified if profile.backup_verified is not None else False,
                key="profile_backup_verified",
            )

        region = st.text_input(
            "地区",
            value=profile.region or loc,
            key="profile_region",
            placeholder="例如：深圳",
        )
        device_model = st.text_input(
            "设备型号",
            value=profile.device_model or "",
            key="profile_device",
            placeholder="例如：KeyGuard Pro",
        )
        preferred_chains = st.text_input(
            "常用链",
            value=profile.preferred_chains or "",
            key="profile_chains",
            placeholder="例如：BTC, ETH, SOL",
        )

        if st.button("💾 保存档案", use_container_width=True):
            new_profile = UserProfile(
                user_id=uid,
                experience_level=experience_level,
                region=region if region else None,
                device_model=device_model if device_model else None,
                preferred_chains=preferred_chains if preferred_chains else None,
                connection_method=connection_method,
                passphrase_enabled=passphrase_enabled,
                backup_verified=backup_verified,
            )
            if save_user_profile(new_profile):
                load_user_profile(uid)
                st.success("✅ 档案已保存")
                st.rerun()
            else:
                st.error("❌ 保存失败，请重试")

    with st.expander("🧠 记忆状态", expanded=True):
        from utils.user_profile import current_profile as _get_profile

        _profile = _get_profile()
        st.markdown("**📝 用户档案**")
        if _profile:
            _parts = []
            if _profile.experience_level:
                _parts.append(_profile.experience_level)
            if _profile.region:
                _parts.append(_profile.region)
            if _profile.device_model:
                _parts.append(_profile.device_model)
            if _profile.preferred_chains:
                _parts.append(_profile.preferred_chains)
            if _profile.connection_method:
                _parts.append(_profile.connection_method)
            if _profile.passphrase_enabled is not None:
                _parts.append("Passphrase 已开启" if _profile.passphrase_enabled else "Passphrase 未开启")
            if _profile.backup_verified is not None:
                _parts.append("备份已验证" if _profile.backup_verified else "备份未验证")
            st.caption(" · ".join(_parts))
        else:
            st.caption("未填写，可在侧边栏填写以获取个性化安全建议")

        st.markdown("**💬 对话记忆**")
        _messages = st.session_state.get("messages", [])
        _user_turns = sum(1 for m in _messages if m.get("role") == "user")
        _max_turns = 6
        if _user_turns > _max_turns:
            st.caption(f"对话轮数：{_user_turns} 轮 · 已触发压缩（保留最近 {_max_turns} 轮）")
        else:
            st.caption(f"对话轮数：{_user_turns} 轮 · 压缩阈值：{_max_turns} 轮")

    if uid == MEMORY_DEMO_USER_ID:
        with st.expander("🧠 压缩摘要（演示）", expanded=False):
            if _user_turns > _max_turns:
                st.caption(f"状态：已触发压缩，保留最近 {_max_turns} 轮完整对话。")
            elif _user_turns:
                st.caption("状态：预置历史已就绪，继续提问后会触发压缩。")
            else:
                st.caption("状态：对话已清空，重新选择 1005 可恢复预置历史。")
            st.markdown(MEMORY_DEMO_SUMMARY)

    st.divider()
    st.markdown("**💡 试试这些问题：**")
    EXAMPLE_QUESTIONS = [
        ("🔋", "硬件钱包开不了机怎么办？"),
        ("🔵", "蓝牙没法连接手机怎么办？"),
        ("🔌", "电脑识别不到设备，怎么排查？"),
        ("🔄", "固件升级中断了怎么办？"),
        ("🧳", "设备丢了或坏了，资产还能恢复吗？"),
        ("🧩", "Passphrase 忘了，为什么恢复后余额为零？"),
    ]
    for icon, q in EXAMPLE_QUESTIONS:
        if st.button(f"{icon}  {q}", key=f"q_{q[:6]}", use_container_width=True):
            st.session_state["pending_prompt"] = q
            st.rerun()


agent = get_or_build_agent()

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if not st.session_state["messages"]:
    with st.chat_message("assistant", avatar="🔐"):
        st.markdown(
            f"""你好，我是 **KeyGuard 硬件钱包智能客服**。我可以帮你：

- 🔋 **设备故障**：开不了机、屏幕不亮、按键卡死、设备锁定
- 🔌 **连接排查**：USB-C、蓝牙、App 识别不到设备等问题
- 🔄 **固件修复**：升级中断、恢复模式、固件验证失败
- 🛡️ **备份安全**：助记词备份、设备丢失、恢复钱包
- ⛓️ **交易边界**：签名后 pending、手续费和链网络状态的区分
- 📊 **安全报告**：基于模拟使用记录生成月度风险建议

> 当前登录身份：**{selected}**，切换用户会自动开新对话。"""
        )

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"], avatar="🔐" if msg["role"] == "assistant" else "🧑"):
        st.markdown(msg["content"])

prompt = st.chat_input("输入你的问题，例如：硬件钱包开不了机或蓝牙连不上怎么办？")
if not prompt and st.session_state.get("pending_prompt"):
    prompt = st.session_state["pending_prompt"]
    st.session_state["pending_prompt"] = None

if prompt:
    if agent is None:
        st.error("⚠️ 模型服务暂不可用，请联系项目作者")
    else:
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)
        st.session_state["messages"].append({"role": "user", "content": prompt})

        with st.chat_message("assistant", avatar="🔐"):
            status = st.status("🤔 正在分析...", expanded=True)
            answer_placeholder = st.empty()

            answer_text = ""
            step_idx = 0
            status_finalized = False

            try:
                active_profile = ProfileDatabase().get_profile(uid)
                for kind, content in agent.execute_stream(
                    prompt,
                    st.session_state.get("messages", []),
                    user_id=uid,
                    location=loc,
                    user_profile=active_profile,
                ):
                    if kind == "answer":
                        if not status_finalized:
                            status.update(label="✅ 分析完成", state="complete", expanded=False)
                            status_finalized = True
                        answer_text += content
                        answer_placeholder.markdown(answer_text)
                    else:
                        step_idx += 1
                        if kind == "thought":
                            status.update(label=f"💭 正在判断问题类型（第 {step_idx} 步）...")
                            status.markdown(f"**💭 思考**：{content}")
                        elif kind == "tool_call":
                            status.update(label=f"🔧 正在调用工具（第 {step_idx} 步）...")
                            status.markdown(content)
                        elif kind == "tool_result":
                            status.update(label=f"📥 获取到信息（第 {step_idx} 步）...")
                            status.markdown(content)
            except Exception as e:
                logger.error(f"[app]Agent 响应失败：{e}", exc_info=True)
                answer_text = format_agent_error(e)
                answer_placeholder.markdown(answer_text)
                status.update(label="⚠️ 生成失败", state="error", expanded=False)
                status_finalized = True

            if not answer_text:
                answer_text = "⚠️ 未能生成有效回答，请重试或换一种问法。"
                answer_placeholder.markdown(answer_text)
                status.update(label="⚠️ 未能生成有效回答", state="error", expanded=False)
            elif not status_finalized:
                status.update(label="✅ 分析完成", state="complete", expanded=False)

        st.session_state["messages"].append({"role": "assistant", "content": answer_text})
