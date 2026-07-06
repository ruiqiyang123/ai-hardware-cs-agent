<div align="center">

# 智扫通 AI Hardware CS Agent

**面向智能硬件售后的 Agentic RAG 客服系统**

以扫地机器人为例，展示如何用 LangGraph ReAct Agent + RAG 构建具备检索增强、工具调用、报告生成能力的 AI 客服应用。

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-green)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6-orange)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-red)](https://streamlit.io/)
[![CI](https://github.com/ruiqiyang123/ai-hardware-cs-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/ruiqiyang123/ai-hardware-cs-agent/actions/workflows/ci.yml)

</div>

---

## 概述

本项目是一个 **Agentic RAG 客服系统** demo，聚焦智能硬件售后场景。用户通过 Streamlit 网页界面提问，ReAct Agent 自主判断意图、选择工具、检索知识库并生成回答，也能拉取外部业务数据生成个性化使用报告。

项目重点演示三类能力：

| 能力 | 说明 |
|------|------|
| **RAG 知识库** | PDF/TXT 文档 → Chroma 向量库 → 检索 + LLM 总结，答案自动标注来源 |
| **Agent 工具调用** | ReAct 链路自主决定调用哪些工具，普通问答与报告生成走不同提示词 |
| **会话级用户上下文** | 前端切换用户后，Agent 读到的是当前会话绑定的 ID/位置，而非随机值 |

## 快速体验

### 🚀 在线体验（零门槛，无需 API Key）

👉 **[ai-hardware-cs-agent.streamlit.app](https://ai-hardware-cs-agent.streamlit.app)**

打开链接即可直接使用，**无需注册、无需配置 API Key**。点击侧边栏的示例问题，或自己输入问题，几秒内就能看到 Agent 的实时推理过程与最终回答。

**建议体验这几个场景**：

| 场景 | 示例问题 | 看点 |
|------|----------|------|
| 🔧 故障排查 | 扫地机器人无法正常回充，该怎么排查？ | RAG 检索知识库 + 答案末尾标注参考来源 |
| 🌤️ 天气适配 | 我所在城市的天气适合拖地吗？ | Agent 调用真实天气 API（Open-Meteo） |
| 📊 个性化报告 | 帮我生成本月使用报告，并给出保养建议 | 多步链路：取用户ID → 当前月 → 切换报告模式 → 查使用记录 |
| 🔄 用户切换 | 侧边栏切换"王先生（杭州）"后再问天气 | 会话级位置上下文，Agent 用当前用户的城市 |

> 💡 共享 API Key 的额度有限，请合理使用。如果遇到限额，可以参考下方"本地启动"自行运行。

### 💻 本地启动

```bash
# 1. 克隆项目
git clone https://github.com/ruiqiyang123/ai-hardware-cs-agent.git
cd ai-hardware-cs-agent

# 2. 创建虚拟环境
python -m venv .venv && source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API Key（二选一）
export DASHSCOPE_API_KEY="your-key"         # 阿里云百炼（默认，含 Embedding）
# 或 export MIMO_API_KEY="your-key"         # 小米 MiMo，搭配本地 embedding

# 5. 初始化知识库 → 启动
python scripts/init_knowledge_base.py
streamlit run app.py
```

访问 `http://localhost:8501`。

## 功能展示

### 1. RAG 知识库问答

输入售后问题，Agent 自动检索相关文档并生成回答，末尾标注来源：

```
Q: 扫地机器人无法正常回充，该怎么排查？
A: 请按以下步骤排查：
   1. 检查充电座是否通电...
   2. 清洁充电触点...
   ...
📚 参考来源：故障排除.txt、扫地机器人100问.pdf
```

### 2. 天气场景化建议

Agent 可获取真实天气数据（Open-Meteo 免费 API），判断当前湿度/降水量是否适合拖地：

```
Q: 我所在城市的天气适合拖地吗？
A: 深圳当前气温 28°C，湿度 78%，降水量 0.5mm。湿度偏高，建议...
```

### 3. 个性化使用报告

Agent 按固定链路（获取用户 ID → 月份 → 切换报告模式 → 拉取使用记录）生成报告：

```
Q: 帮我生成本月使用报告
A: 📊 张先生 2025-06 使用报告
   - 日均清扫面积: 42㎡
   - HEPA滤网: 剩余 70%
   - 保养建议: ...
```

## 系统架构

```
用户输入 (Streamlit Web UI)
    │
    ▼
┌──────────────────────────────────────────┐
│            ReactAgent                     │
│  LangGraph ReAct + 动态提示词中间件        │
│                                           │
│  工具列表:                                │
│  ┌─ rag_summarize ─→ Chroma 向量库 ─→ LLM  │
│  ├─ get_weather ─→ Open-Meteo API         │
│  ├─ get_user_location ─→ 会话上下文/IP    │
│  ├─ get_user_id / get_current_month       │
│  ├─ fetch_external_data ─→ CSV 使用记录    │
│  └─ fill_context_for_report → 提示词切换   │
└──────────────────────────────────────────┘
    │                        │
    ▼                        ▼
 知识库文档          外部业务数据 (CSV)
 (PDF / TXT)
```

模型支持：
- **Chat**：阿里云百炼 `ChatTongyi`（默认） / 小米 MiMo `ChatOpenAI` 兼容接口
- **Embedding**：DashScope `text-embedding-v4` / 本地哈希 Embedding（无 key 时跑通 demo）

## 工具说明

| 工具 | 用途 |
|------|------|
| `rag_summarize` | 从向量库检索售后资料并 LLM 总结 |
| `get_weather` | Open-Meteo 实时天气（带重试机制） |
| `get_user_location` | 会话位置优先，IP 定位兜底 |
| `get_user_id` | 当前会话用户 ID |
| `get_current_month` | 系统当前月份 |
| `fetch_external_data` | 查询指定用户月份的使用记录 |
| `fill_context_for_report` | 触发报告生成提示词切换 |

## 项目结构

```
ai-hardware-cs-agent/
├── app.py                          # Streamlit 入口
├── agent/
│   ├── react_agent.py              # LangGraph ReAct Agent 封装
│   └── tools/
│       ├── agent_tools.py          # 7 个工具（委托给服务模块）
│       └── middleware.py           # 动态提示词切换中间件
├── rag/
│   ├── vector_store.py             # Chroma 向量库 + 文档加载
│   ├── rag_service.py              # RAG 总结 + 引用溯源
│   └── source_formatter.py         # 来源提取/格式化（纯逻辑）
├── agent/services/
│   ├── weather_service.py          # 天气 API（可独立单测）
│   └── usage_records.py            # CSV 解析（可独立单测）
├── model/
│   ├── factory.py                  # ChatModel / Embedding 工厂
│   └── local_embeddings.py         # 本地哈希 Embedding
├── config/                         # YAML 业务配置
├── prompts/                        # 提示词模板
├── utils/
│   ├── retry.py                    # 通用重试装饰器
│   ├── session_context.py          # 会话级用户上下文
│   └── ...
├── eval/
│   ├── eval_cases.json             # 30 题评测集
│   ├── run_eval.py                 # 评测脚本（支持 --record）
│   ├── compare.py                  # 前后对比
│   └── trend.py                    # 评测趋势查看
├── scripts/
│   ├── init_knowledge_base.py      # 知识库初始化
│   └── generate_records.py         # 使用记录生成器
├── tests/                          # 单元测试（17 个用例）
├── .github/workflows/ci.yml        # GitHub Actions CI
└── data/                           # 知识库文档 + CSV
```

## 测试与 CI

项目包含 17 个单元测试，覆盖天气 API、CSV 解析、来源格式化、会话上下文、评测评分、评测事件流兼容等模块。CI 在每次 push / PR 时自动运行：

```bash
# 本地运行测试
python -m pytest tests/ -v

# 评测
python eval/run_eval.py --tag after --record
python eval/compare.py before after
python eval/trend.py                 # 查看历史趋势
```

## 已完成的优化

| 优化项 | 说明 |
|--------|------|
| 真实数据接入 | Mock 天气 → Open-Meteo API，Mock 位置 → 会话上下文 + IP 定位 |
| 会话级模型隔离 | 移除 `os.environ` provider 路由，改为显式构建注入，侧边栏切换真正生效 |
| 引用溯源 | RAG 答案自动标注知识库文档来源 |
| 服务模块抽离 | 天气/CSV/格式化逻辑独立成可单测模块，`@tool` 仅负责声明+委托 |
| 外部 API 重试 | 通用 `with_retry` 装饰器，指数退避覆盖瞬时网络抖动 |
| 思考过程可视化 | `st.status` 实时容器展示 Agent 推理步骤（💭思考 → 🔧调用工具 → 📥结果），出答案时自动收起 |
| 动态数据范围 | `records.csv` 月份动态生成到当月，耗材采用「递减+换件回升」模型贴近真实 |
| 评测体系 | 30 题评测集 + 前后对比 + 趋势记录 + CI 自动验证 |
| 零门槛在线体验 | Streamlit Cloud 部署 + 共享 API Key Secret，访客无需配置即可使用 |

## 配置说明

| 文件 | 说明 |
|------|------|
| `config/rag.yml` | Chat 模型名 + Embedding 模型名 |
| `config/chroma.yml` | 集合名、持久化路径、分块参数、Top-K |
| `config/prompts.yml` | 各类提示词路径 |
| `config/agent.yml` | 外部数据路径等业务配置 |

## 许可

MIT
