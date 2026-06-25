import os

import streamlit as st

from agent.react_agent import ReactAgent
from agent.tools.agent_tools import configure_rag_model
from model.factory import build_chat_model
from utils.logger_handler import logger
from utils.session_context import set_location, set_user_id

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
}

with st.sidebar:
    st.header("👤 测试用户")
    selected = st.selectbox("当前登录用户", list(USER_OPTIONS.keys()), key="user_select")
    uid, loc = USER_OPTIONS[selected]
    set_user_id(uid)
    set_location(loc)
    st.caption(f"用户 ID `{uid}`　·　位置 `{loc}`")

    # 切换用户时清空对话历史（避免上下文混淆）
    if st.session_state.get("active_user") != selected:
        st.session_state["active_user"] = selected
        st.session_state["messages"] = []

    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

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

            for kind, content in agent.execute_stream(prompt):
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
