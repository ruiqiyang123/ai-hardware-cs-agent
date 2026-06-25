import streamlit as st
import os
from agent.react_agent import ReactAgent
from agent.tools.agent_tools import configure_rag_model
from model.factory import build_chat_model
from utils.session_context import set_user_id, set_location
from utils.logger_handler import logger

# ============================================================
# Streamlit Cloud & 本地环境兼容配置
# 支持环境变量 + 侧边栏手动配置两种方式
# ============================================================

# 检查是否有环境变量API Key
env_dashscope_key = os.getenv("DASHSCOPE_API_KEY")
env_mimo_key = os.getenv("MIMO_API_KEY")

st.set_page_config(page_title="智扫通 · 智能客服", page_icon="🤖")
st.title("🤖 智扫通机器人智能客服")
st.caption("基于 LangChain ReAct Agent + RAG 检索增强")
st.divider()

# ============================================================
# 侧边栏：API Key 配置
# 部署后用户可以输入临时API Key直接体验
# ============================================================
with st.sidebar:
    st.header("⚙️ API Key 配置")

    # 提供配置指引
    if not env_dashscope_key and not env_mimo_key:
        with st.expander("📖 如何获取API Key?", expanded=False):
            st.markdown("""
            **方式1：阿里云百炼（推荐）**
            - 访问：https://bailian.console.aliyun.com/
            - 登录后创建 API Key
            - 复制到下方输入框

            **方式2：小米MiMo（免费额度）**
            - 访问：https://mimo.xiaomi.com/
            - 注册后获取 Token Plan API Key
            - Base URL: `https://token-plan-sgp.xiaomimimo.com/v1`
            """)

        # DashScope 配置
        st.subheader("阿里云 DashScope")
        dashscope_key = st.text_input(
            "DashScope API Key",
            type="password",
            help="申请地址：https://bailian.console.aliyun.com/"
        )

        st.divider()

        # MiMo 配置
        st.subheader("小米 MiMo")
        mimo_key = st.text_input(
            "MiMo API Key",
            type="password",
            help="申请地址：https://mimo.xiaomi.com/"
        )
        mimo_base_url = st.text_input(
            "MiMo Base URL",
            value="https://token-plan-sgp.xiaomimimo.com/v1",
            help="默认 Token Plan 新加坡节点"
        )

        if not dashscope_key and not mimo_key:
            st.warning("⚠️ 请配置 API Key 以正常使用")

        st.divider()
    else:
        st.success("✅ 已配置共享 API Key，可直接体验")
        if env_dashscope_key:
            st.caption("模型：阿里云百炼 Qwen")
        elif env_mimo_key:
            st.caption("模型：小米 MiMo")
        st.caption("💡 共享额度有限，请合理使用")
        dashscope_key = env_dashscope_key
        mimo_key = env_mimo_key
        mimo_base_url = os.getenv("MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1")


# ============================================================
# 会话级模型构建（替代原 os.environ 进程级路由）
#
# 改造点：原版本在侧边栏用 os.environ["CHAT_PROVIDER"] 切换 provider，
# 但 model.factory 在导入时已构建单例 chat_model，运行时改 env 不生效，
# 且多会话共享进程级 env 存在串号风险。
#
# 现改为：按当前配置显式 build_chat_model 构建，注入 ReactAgent 与
# RAG 服务，并按配置签名缓存 agent，切换 provider/Key 后自动重建。
# ============================================================
def resolve_chat_config() -> tuple[dict, str]:
    """从侧边栏 / 环境变量解析当前应使用的 chat 模型配置。

    返回 (build_kwargs, config_signature)：
    - build_kwargs 传给 build_chat_model；
    - config_signature 用作 session_state 缓存键，变更即重建 agent。
    """
    if mimo_key:
        kwargs = {
            "provider": "mimo",
            "api_key": mimo_key,
            "base_url": mimo_base_url,
            "model_name": os.getenv("MIMO_CHAT_MODEL"),
        }
        sig = f"mimo:{mimo_key}:{mimo_base_url}"
    elif dashscope_key:
        # DashScope 的 key 仍需写入 env，ChatTongyi 在调用时读取
        os.environ["DASHSCOPE_API_KEY"] = dashscope_key
        kwargs = {"provider": "dashscope"}
        sig = f"dashscope:{dashscope_key}"
    else:
        kwargs = {}
        sig = "default"

    return kwargs, sig


def get_or_build_agent() -> ReactAgent:
    kwargs, sig = resolve_chat_config()

    cached_sig = st.session_state.get("agent_config_sig")
    if "agent" in st.session_state and cached_sig == sig:
        return st.session_state["agent"]

    # 配置变更（或首次）：构建模型 → 注入 RAG → 构建 Agent
    try:
        chat_model = build_chat_model(**kwargs)
        configure_rag_model(chat_model)
        # 首次部署时 chroma_db 是空的（gitignore），需要从 data/ 加载文档建索引。
        # 加锁防止 Streamlit rerun 触发并发初始化。
        _ensure_knowledge_base_loaded()
        st.session_state["agent"] = ReactAgent(chat_model=chat_model)
        st.session_state["agent_config_sig"] = sig
        logger.info(f"[app]重建 Agent，配置签名={sig}")
    except ValueError as e:
        st.error(f"模型配置错误：{e}")
        if "agent" not in st.session_state:
            st.session_state["agent"] = None
    return st.session_state.get("agent")


@st.cache_resource(show_spinner="📚 首次启动正在初始化知识库（约 30-60 秒）...")
def _ensure_knowledge_base_loaded() -> bool:
    """首次部署时自动把 data/ 下的文档加载进 Chroma。

    chroma_db/ 被 .gitignore，Streamlit Cloud 部署后向量库是空的。
    用 @st.cache_resource 保证整个 server 进程只跑一次，且并发 rerun 不会重入。
    向量库通过 MD5 文件去重，重复跑也是幂等的。
    """
    from rag.vector_store import VectorStoreService
    VectorStoreService().load_document()
    return True


# ============================================================
# 侧边栏：会话级用户上下文（替代原 random mock）
# 改造点：真实产品里，用户登录后 ID/位置在会话内是固定的。
# 前端侧边栏切换用户后，会同步写入 session_context，
# Agent 调用 get_user_id / get_user_location 工具时读到的是当前登录用户。
# ============================================================
with st.sidebar:
    st.header("👤 当前会话")
    user_options = {
        "1001 - 张先生（深圳）": ("1001", "深圳"),
        "1002 - 李女士（合肥）": ("1002", "合肥"),
        "1003 - 王先生（杭州）": ("1003", "杭州"),
        "1004 - 陈女士（北京）": ("1004", "北京"),
    }
    selected = st.selectbox("当前登录用户", list(user_options.keys()))
    uid, loc = user_options[selected]
    set_user_id(uid)
    set_location(loc)
    st.caption(f"用户ID：`{uid}`　位置：`{loc}`")
    st.divider()
    st.markdown("**试试这些问题：**")
    st.markdown("- 扫地机器人无法正常回充，该怎么排查？")
    st.markdown("- 我所在城市的天气适合拖地吗？")
    st.markdown("- 帮我生成本月机器人使用报告，并给出保养建议。")

# 构建会话级 Agent
agent = get_or_build_agent()

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state["messages"]:
    st.chat_message(message["role"]).write(message["content"])

prompt = st.chat_input()

if prompt:
    if agent is None:
        st.error("⚠️ 请先在侧边栏配置 API Key")
    else:
        st.chat_message("user").write(prompt)
        st.session_state["messages"].append({"role": "user", "content": prompt})

        response_messages: list[str] = []
        with st.spinner("智能客服思考中..."):
            res_stream = agent.execute_stream(prompt)

            def stream_generator(generator, cache_list):
                """逐字流式输出，同时缓存完整响应"""
                for chunk in generator:
                    cache_list.append(chunk)
                    for char in chunk:
                        yield char

            st.chat_message("assistant").write_stream(stream_generator(res_stream, response_messages))
            st.session_state["messages"].append({"role": "assistant", "content": "".join(response_messages)})
            st.rerun()
