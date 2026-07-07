<div align="center">

# 智扫通 AI Hardware CS Agent

**面向扫地机器人售后的 Agentic RAG 智能客服 Demo**

用 LangGraph ReAct Agent、LangChain 工具链、Chroma RAG 和 Streamlit，构建一个可在线体验的智能硬件售后客服应用。

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-green)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6-orange)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-red)](https://streamlit.io/)
[![CI](https://github.com/ruiqiyang123/ai-hardware-cs-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/ruiqiyang123/ai-hardware-cs-agent/actions/workflows/ci.yml)

[在线体验](https://ai-hardware-cs-agent.streamlit.app/) · [部署说明](./DEPLOYMENT.md)

</div>

---

## 项目定位

这是一个面向智能硬件售后场景的 Agentic RAG 智能客服 Demo。项目以扫地机器人 / 扫拖一体机为例，模拟用户在故障排查、维护保养、选购建议、环境适配和月度使用报告中的咨询流程。

项目覆盖一个智能客服应用从用户问题、Agent 决策、工具调用、知识库检索到最终回答生成的完整链路：

| 能力 | 当前实现 |
|------|----------|
| Agent 决策 | LangGraph `create_react_agent`，模型根据用户意图自主选择工具 |
| RAG 问答 | TXT / PDF 知识库入库、分块、Embedding、Chroma 检索、答案引用溯源 |
| 工具调用 | 天气、用户位置、用户 ID、用户档案、当前月份、CSV 使用记录、报告模式切换 |
| 动态 Prompt | 普通客服问答和月度报告生成使用不同系统提示词 |
| 会话上下文 | 侧边栏切换测试用户后，Agent 读取稳定的用户 ID、城市和档案 |
| 记忆压缩 | 超过 6 轮对话后压缩旧消息，保留最近上下文 |
| 评测闭环 | 30 题关键词评测集、运行脚本、前后对比脚本、趋势记录脚本 |
| 工程验证 | 36 个 pytest 测试，覆盖 RAG、工具、配置、错误提示、事件流等模块 |

## 在线体验

地址：[https://ai-hardware-cs-agent.streamlit.app/](https://ai-hardware-cs-agent.streamlit.app/)

当前线上 Demo 使用：

- **Chat 模型：** MiMo `mimo-v2.5-pro`
- **Embedding：** 本地 1024 维 Hash Embedding
- **向量库：** Chroma，本地持久化目录 `chroma_db/`
- **前端：** Streamlit Chat UI

线上页面已经预配置模型服务，访客打开即可测试，不需要在页面里填写 API Key。侧边栏只展示当前模型 ID、测试用户、用户档案和记忆状态，不展示后台配置状态。

建议测试这几个问题：

| 场景 | 示例问题 | 可观察点 |
|------|----------|----------|
| 故障排查 | 扫地机器人无法正常回充，该怎么排查？ | Agent 调用 RAG，答案末尾保留参考来源 |
| 宠物家庭保养 | 家里有宠物，应该怎么维护主刷和滤网？ | 调用用户档案，输出个性化建议 |
| 天气适配 | 我所在城市的天气适合拖地吗？ | 读取当前会话城市，再调用 Open-Meteo 天气 API |
| 月度报告 | 帮我生成本月使用报告，并给出保养建议。 | 按用户 ID、月份、CSV 使用记录生成报告 |
| 记忆压缩 | 切换到 `1005 - 赵先生（成都）` | 预置多轮历史，用于演示对话压缩 |

## 产品边界

为避免把 Demo 包装成真实商业系统，项目边界说明如下：

- `data/external/records.csv` 是模拟外部业务系统数据，不代表真实用户数据。
- 线上 Demo 是演示环境，不承诺生产级并发、监控、审计和 SLA。
- 评测脚本可用于跑真实结果，但仓库目前不提交 `eval_results/`，效果数据需要以实际运行结果为准。
- 本项目重点展示 Agent、RAG、工具调用、Prompt、评测和 Demo 产品化能力。

## 系统架构

```text
用户问题
  -> Streamlit Chat UI
  -> 会话上下文：用户 ID / 城市 / 用户档案 / 历史对话
  -> ReactAgent
     -> LangGraph ReAct Agent
     -> 动态系统 Prompt
     -> 消息压缩
  -> 工具调用
     -> rag_summarize：Chroma RAG + LLM 总结 + 引用来源
     -> get_weather：Open-Meteo 天气数据
     -> get_user_location：会话城市，IP 定位兜底
     -> get_user_id：当前测试用户 ID
     -> get_user_profile：SQLite 用户档案
     -> get_current_month：系统当前月份
     -> fetch_external_data：CSV 使用记录
     -> fill_context_for_report：报告模式切换信号
  -> MiMo 模型整合工具结果
  -> 输出售后答复或月度报告
```

## RAG 流程

```text
data/ 下的 TXT / PDF 文件
  -> txt_loader / pdf_loader
  -> RecursiveCharacterTextSplitter
  -> Embedding 向量化
  -> Chroma 持久化
  -> 用户提问时 Top-K 检索
  -> 关键词兜底召回
  -> rag_summarize Prompt
  -> LLM 基于参考资料生成答案
  -> 追加“参考来源：xxx.txt、yyy.pdf”
```

当前 Chroma 配置见 [config/chroma.yml](./config/chroma.yml)：

- `chunk_size: 200`
- `chunk_overlap: 20`
- `k: 3`
- 支持文件类型：`txt`、`pdf`

## LangGraph 和 LangChain 分工

| 组件 | 在项目里的作用 |
|------|----------------|
| LangGraph `create_react_agent` | 编排 ReAct 循环，让模型在“思考、调用工具、观察结果、生成回答”之间循环 |
| LangChain `@tool` | 把 Python 函数声明为 Agent 可调用工具 |
| LangChain `ChatOpenAI` | 通过 OpenAI 兼容接口接入 MiMo |
| LangChain `PromptTemplate` | 构建 RAG 总结 Prompt |
| LangChain `StrOutputParser` | 把模型输出解析为字符串 |
| LangChain `Document` | 表示知识库切分后的文档片段 |
| LangChain `RecursiveCharacterTextSplitter` | 对 TXT / PDF 文本进行递归分块 |
| LangChain Chroma 集成 | 连接本地 Chroma 向量库，实现检索器 |
| LangChain Embeddings 接口 | 自定义 `LocalHashEmbeddings`，保证无 Embedding Key 时也能跑通 Demo |

## 代码导览

| 文件 / 目录 | 作用 |
|-------------|------|
| [app.py](./app.py) | Streamlit 入口，负责页面、测试用户、模型配置、聊天渲染和状态展示 |
| [agent/react_agent.py](./agent/react_agent.py) | 封装 LangGraph ReAct Agent，输出 `thought`、`tool_call`、`tool_result`、`answer` 四类事件 |
| [agent/tools/agent_tools.py](./agent/tools/agent_tools.py) | Agent 工具声明层，保留 `@tool` 封装，业务逻辑委托给服务模块 |
| [agent/tools/profile_tools.py](./agent/tools/profile_tools.py) | 用户档案工具，让 Agent 获取家庭面积、宠物、地毯、设备型号等信息 |
| [agent/tools/middleware.py](./agent/tools/middleware.py) | 动态 Prompt 中间件，识别报告模式并切换提示词 |
| [agent/services/weather_service.py](./agent/services/weather_service.py) | Open-Meteo 地理编码和天气查询服务 |
| [agent/services/usage_records.py](./agent/services/usage_records.py) | CSV 使用记录读取、解析和月份兜底 |
| [agent/services/memory_compression.py](./agent/services/memory_compression.py) | 对话历史压缩，超过阈值后保留最近 6 轮 |
| [rag/rag_service.py](./rag/rag_service.py) | RAG 总结主链路，负责检索、关键词兜底、LLM 总结和来源拼接 |
| [rag/vector_store.py](./rag/vector_store.py) | Chroma 向量库、文档加载、MD5 去重和文本分块 |
| [rag/source_formatter.py](./rag/source_formatter.py) | 从 metadata 中提取并格式化引用来源 |
| [model/factory.py](./model/factory.py) | Chat / Embedding 工厂，支持 MiMo、DashScope 和本地 Hash Embedding |
| [model/local_embeddings.py](./model/local_embeddings.py) | 本地轻量 Embedding，方便无外部 Embedding Key 时运行 |
| [database/profile_db.py](./database/profile_db.py) | SQLite 用户档案存储 |
| [utils/model_config.py](./utils/model_config.py) | 模型配置解析和安全签名，避免把完整 API Key 写入日志 |
| [eval/](./eval) | 30 题评测集、运行脚本、对比脚本和趋势脚本 |
| [tests/](./tests) | pytest 单元测试，目前 36 个用例 |

## 工具列表

| 工具 | 触发场景 | 数据来源 |
|------|----------|----------|
| `rag_summarize` | 故障、保养、选购、产品知识问答 | `data/` 知识库 + Chroma |
| `get_weather` | 天气、湿度、是否适合拖地 | Open-Meteo Forecast + Geocoding API |
| `get_user_location` | 需要当前用户城市 | Streamlit 会话上下文，IP 定位兜底 |
| `get_user_id` | 需要当前登录用户 | Streamlit 侧边栏选择 |
| `get_user_profile` | 个性化选购 / 保养建议 | SQLite 用户档案 |
| `get_current_month` | 生成本月报告 | 系统当前时间 |
| `fetch_external_data` | 生成使用报告 | `data/external/records.csv` |
| `fill_context_for_report` | 报告生成前置步骤 | 工具返回信号，触发动态 Prompt |

## 本地启动

### 1. 克隆项目

```bash
git clone https://github.com/ruiqiyang123/ai-hardware-cs-agent.git
cd ai-hardware-cs-agent
```

### 2. 创建虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置环境变量

推荐复制 `.env.example` 为 `.env`，然后填入自己的 MiMo API Key：

```bash
cp .env.example .env
```

关键配置：

```bash
MIMO_API_KEY=your-mimo-api-key
MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
MIMO_CHAT_MODEL=mimo-v2.5-pro
CHAT_PROVIDER=mimo
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_DIMENSION=1024
```

### 4. 初始化知识库并启动

```bash
python scripts/init_knowledge_base.py
streamlit run app.py
```

打开 `http://localhost:8501`。

## 评测与测试

### 单元测试

```bash
python -m pytest tests/ -v
```

当前测试覆盖：

- 模型配置和 API Key 签名脱敏
- Streamlit Demo 是否固定使用 MiMo
- RAG 来源提取和关键词兜底
- 天气服务解析
- CSV 使用记录解析
- 会话上下文稳定性
- LangGraph 事件流兼容
- RAG 短路策略
- Prompt 合约和错误提示

### RAG / Agent 效果评测

```bash
python eval/run_eval.py --tag before --record
python eval/run_eval.py --tag after --record
python eval/compare.py before after
python eval/trend.py
```

评测集位于 [eval/eval_cases.json](./eval/eval_cases.json)，目前包含 30 道题，覆盖：

- 故障排查：10 题
- 维护保养：9 题
- 选购建议：11 题

评测方式是关键词覆盖率，适合用于比较 Prompt、分块参数、Top-K、知识库内容调整前后的变化。它不能完全代表真实用户满意度，但可以作为迭代优化的量化参考。

## 部署

项目已按 Streamlit Cloud 部署方式组织：

- 入口文件：`app.py`
- Python 版本：3.11
- 依赖文件：`requirements.txt`
- 线上 Secret：在 Streamlit Cloud 控制台配置 `MIMO_API_KEY` 等环境变量

详细步骤见 [DEPLOYMENT.md](./DEPLOYMENT.md)。

## 项目结构

```text
ai-hardware-cs-agent/
├── app.py
├── agent/
│   ├── react_agent.py
│   ├── message_builder.py
│   ├── stream_policy.py
│   ├── services/
│   │   ├── memory_compression.py
│   │   ├── usage_records.py
│   │   └── weather_service.py
│   └── tools/
│       ├── agent_tools.py
│       ├── middleware.py
│       └── profile_tools.py
├── config/
├── data/
│   └── external/records.csv
├── database/
├── eval/
├── model/
├── prompts/
├── rag/
├── scripts/
├── tests/
├── DEPLOYMENT.md
├── MEMORY_IMPLEMENTATION.md
└── README.md
```

## 许可说明

本仓库目前未附带单独的 `LICENSE` 文件；如后续需要作为正式开源项目复用，可再补充许可证文件。
