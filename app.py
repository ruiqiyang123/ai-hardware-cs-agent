import streamlit as st
import os
from agent.react_agent import ReactAgent
from utils.session_context import set_user_id, set_location

# ============================================================
# Streamlit Cloud & 本地环境兼容配置
# 支持环境变量 + 侧边栏手动配置两种方式
# ============================================================

# 检查是��有环境变量API Key
env_dashscope_key = os.getenv("DASHSCOPE_API_KEY")
env_mimo_key = os.getenv("MIMO_API_KEY")

st.set_page_config(page_title="智扫通 · 智能客服", page_icon="🤖")
st.title("🤖 智扫通机器人智能客服")
st.caption("基于 LangChain ReAct Agent + RAG 检索增强")
st.divider()

# ============================================================
# 侧边栏：API Key 配置（优先级最高）
# 部署后用户可以输入临时API Key直接体验
# ============================================================
with st.sidebar:
    st.header("⚙️ API Key 配置")

    # 提供配置指引
    if not env_dashscope_key and not env_mimo_key:
        with st.expander("📖 如何获取API Key?", expanded=False):
            st.markdown("""
            **方式1：阿里云百炼（推荐��**
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

        if dashscope_key:
            os.environ["DASHSCOPE_API_KEY"] = dashscope_key
            os.environ["CHAT_PROVIDER"] = "dashscope"
            os.environ["EMBEDDING_PROVIDER"] = "dashscope"
            st.success("✅ DashScope API Key 已设置")

        st.divider()

        # MiMo 配置
        st.subheader("小米 MiMo")
        mimo_key = st.text_input(
            "MiMo API Key",
            type="password",
            help="申请地址：https://mimo.xiaomi.com/"
        )
        if mimo_key:
            os.environ["MIMO_API_KEY"] = mimo_key
            os.environ["CHAT_PROVIDER"] = "mimo"
            os.environ["EMBEDDING_PROVIDER"] = "local"
            st.success("✅ MiMo API Key 已设置")

        # 检查是否有配置
        if not dashscope_key and not mimo_key:
            st.warning("⚠️ 请配置 API Key 以正常使用")

        st.divider()
    else:
        st.info("✅ 已检测到环境变量中的API Key")
        if env_dashscope_key:
            st.text("使用：DashScope")
        elif env_mimo_key:
            st.text("使用：MiMo")

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

# 初始化 Agent
if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state["messages"]:
    st.chat_message(message["role"]).write(message["content"])

prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})

    response_messages: list[str] = []
    with st.spinner("智能客服思考中..."):
        res_stream = st.session_state["agent"].execute_stream(prompt)

        def stream_generator(generator, cache_list):
            """逐字流式输出，同时缓存完整响应"""
            for chunk in generator:
                cache_list.append(chunk)
                for char in chunk:
                    yield char

        st.chat_message("assistant").write_stream(stream_generator(res_stream, response_messages))
        st.session_state["messages"].append({"role": "assistant", "content": "".join(response_messages)})
        st.rerun()
