<div align="center">

# Smart Hardware RAG Agent

**面向智能硬件售后的 Agentic RAG 客服系统**

[![Python](https://img.shields.io/badge/Python-3.11%20recommended-blue)](https://www.python.org/)
&nbsp;
[![LangChain](https://img.shields.io/badge/LangChain-0.3-green)](https://www.langchain.com/)
&nbsp;
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6-orange)](https://github.com/langchain-ai/langgraph)
&nbsp;
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-red)](https://streamlit.io/)

**🚀 [在线体验](https://smart-hardware-rag-agent.streamlit.app)** | **⭐ [GitHub仓库](https://github.com/ruiqiyang123/smart-hardware-rag-agent)**

</div>

---

## 项目简介

Smart Hardware RAG Agent 是一个面向智能硬件售后场景的 AI Agent 应用项目。项目以扫地机器人/扫拖一体机的售后咨询为示例，围绕“用户提问 - 意图判断 - 工具调用 - 知识库检索 - 答案生成 - 使用报告输出”构建完整的 Agentic RAG 流程。

这个项目重点展示三类能力：

- 用 RAG 将产品知识、故障排查、维护保养、选购指南等非结构化资料接入问答流程。
- 用 ReAct Agent 根据用户意图自主选择工具，例如知识库检索、用户信息获取、外部数据查询和报告生成。
- 用中间件和提示词配置管理不同业务场景，让普通问答和个性化报告生成走不同的响应策略。

当前版本聚焦核心链路演示，已实现知识库管理、引用溯源、评测集和稳定的产品化交互，后续会继续补充多轮对话记忆、文档管理和Badcase分析功能。

## 项目亮点

| 亮点 | 说明 |
|---|---|
| 🚀 **在线体验** | 已部署到 Streamlit Cloud，无需克隆代码即可体验 |
| 🤖 **多步推理** | 基于 LangGraph + ReAct 的智能 Agent，自主决策工具调用 |
| 📚 **知识库检索** | Chroma 向量库 + MD5 去重，支持 PDF/TXT 文档 |
| 🔍 **引用溯源** | 答案自动标注来源，提升可信度 |
| 👤 **用户上下文** | 会话级用户管理，支持个性化报告生成 |
| 🌍 **真实数据** | 集成 Open-Meteo 天气 API、IP 定位 |
| 📊 **评测体系** | 20题评测集 + 自动化对比脚本，量化优化效果 |

## 应用场景

| 场景 | 示例问题 | 系统处理方式 |
|---|---|---|
| 售后知识问答 | “机器人无法回充怎么办？” | 调用 RAG 检索故障处理资料，再生成简洁答复 |
| 维护保养咨询 | “多久需要清理滤网和边刷？” | 检索维护保养知识库，输出操作建议 |
| 选购建议 | “小户型适合买哪类扫地机器人？” | 检索选购指南，结合用户需求总结推荐 |
| 环境适配 | “南方潮湿天气会影响拖地效果吗？” | 可结合位置/天气工具进行场景化回答 |
| 使用报告 | “帮我生成本月使用报告” | 获取用户 ID、月份和外部使用记录，生成报告与建议 |

## 核心能力

| 模块 | 能力说明 |
|---|---|
| Agent 编排 | 基于 ReAct 思路组织“判断 - 工具调用 - 观察 - 回答”的执行链路 |
| RAG 检索 | 使用 Chroma 向量库管理产品资料，支持 txt/pdf 文档加载、分块和 MD5 去重 |
| 工具调用 | 封装知识库检索、天气、用户位置、用户 ID、月份和外部使用记录等工具 |
| 动态提示词 | 根据运行时上下文切换普通问答和报告生成提示词 |
| 数据接入 | 通过 CSV 模拟外部业务系统中的用户使用数据 |
| Web 交互 | 使用 Streamlit 构建流式聊天界面，支持实时输出 |
| 配置管理 | 使用 YAML 管理模型、向量库、提示词和外部数据路径 |

## 系统架构

```text
用户输入
  |
  v
Streamlit Chat UI
  |
  v
ReAct Agent
  |
  +-- 意图判断
  +-- 工具选择
  +-- 中间件监控
  +-- 动态 Prompt 切换
  |
  +--------------------+--------------------+
  |                    |                    |
  v                    v                    v
RAG Service        Business Tools       Prompt Templates
  |                    |                    |
  v                    v                    v
Chroma Vector DB   CSV/User/Weather     QA / Report Prompt
  |
  v
产品知识库文档
```

## RAG 流程

```text
data/ 知识库文件
  |
  v
PDF/TXT Loader
  |
  v
RecursiveCharacterTextSplitter
  |
  v
DashScope Embedding
  |
  v
Chroma 持久化向量库
  |
  v
Retriever Top-K 检索
  |
  v
LLM 总结生成答案
```

## Agent 工具

| 工具 | 用途 |
|---|---|
| `rag_summarize` | 从向量知识库中检索售后资料并总结 |
| `get_weather` | 获取城市天气，用于环境适配类问题 |
| `get_user_location` | 获取用户所在城市 |
| `get_user_id` | 获取当前用户标识 |
| `get_current_month` | 获取报告月份 |
| `fetch_external_data` | 查询用户在指定月份的使用记录 |
| `fill_context_for_report` | 标记报告生成场景，触发动态提示词切换 |

## 效果预览

<div align="center">

<img src="assets/chat1.png" alt="RAG 问答示例" width="85%">

*RAG 知识库问答*

&nbsp;

<img src="assets/chat2.png" alt="Agent 工具调用示例" width="85%">

*Agent 工具调用过程*

&nbsp;

<img src="assets/chat3.png" alt="多步推理示例" width="85%">

*多步推理与中间结果*

</div>

## 技术栈

| 层级 | 技术 |
|---|---|
| 大模型 | Qwen / DashScope `ChatTongyi`；MiMo / OpenAI-compatible `ChatOpenAI` |
| Embedding | DashScope `text-embedding-v4`；本地 hash embedding demo 模式 |
| Agent 框架 | LangChain + LangGraph |
| 向量数据库 | Chroma |
| 文档处理 | PyPDF + LangChain Text Splitters |
| 前端 | Streamlit |
| 配置 | YAML |
| 数据模拟 | CSV |

## 快速体验

### 🚀 在线体验（推荐）

**无需安装任何环境，直接体验：**

[https://smart-hardware-rag-agent.streamlit.app](https://smart-hardware-rag-agent.streamlit.app)

**在线体验步骤���**
1. 打开链接
2. 在侧边栏输入临时 API Key（支持 DashScope 或 MiMo）
3. 选择测试用户
4. 输入示例问题开始体验

### 💻 本地体验

### 环境要求

- Python 3.11 推荐，最低 Python 3.10
- DashScope API Key（用于 Qwen 对话模型和 Embedding 模型）
- 或 MiMo API Key（用于小米 MiMo 聊天模型；可搭配本地 embedding 跑 demo）

### 克隆项目

```bash
git clone https://github.com/ruiqiyang123/smart-hardware-rag-agent.git
cd smart-hardware-rag-agent
```

### 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 安装依赖

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 配置 DashScope API Key

复制环境变量模板：

```bash
cp .env.example .env
```

打开 `.env`，把 `DASHSCOPE_API_KEY` 改成自己的阿里云百炼 API Key：

```bash
DASHSCOPE_API_KEY=your-dashscope-api-key
```

也可以直接在终端导出环境变量：

```bash
export DASHSCOPE_API_KEY="your-dashscope-api-key"
```

Windows CMD：

```bat
set DASHSCOPE_API_KEY=your-dashscope-api-key
```

### 使用小米 MiMo 启动

如果只想使用小米 MiMo 作为聊天模型，可以在 `.env` 中改成：

```bash
CHAT_PROVIDER=mimo
MIMO_API_KEY=your-mimo-api-key
MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
MIMO_CHAT_MODEL=mimo-v2.5-pro
EMBEDDING_PROVIDER=local
```

`EMBEDDING_PROVIDER=local` 用于没有 DashScope Embedding Key 时跑通 demo；如果需要更稳定的语义检索效果，建议继续使用 DashScope Embedding。

### 初始化知识库

```bash
python scripts/init_knowledge_base.py
```

该命令会读取 `data/` 目录下的 txt/pdf 文件，分块后写入本地 Chroma 向量库。

### 启动应用

```bash
streamlit run app.py
```

默认访问地址：

```text
http://localhost:8501
```

## Demo 使用流程

1. 首次运行前，确认 `.env` 中已经配置 `DASHSCOPE_API_KEY`，或按上方方式配置 MiMo。
2. 执行 `python scripts/init_knowledge_base.py` 初始化知识库。
3. 执行 `streamlit run app.py` 打开聊天页面。
4. 先测试普通售后问题，例如“扫地机器人无法正常回充，该怎么排查？”。
5. 再测试报告生成问题，例如“帮我生成本月机器人使用报告，并给出保养建议。”。
6. 如果更换了 `data/` 目录下的知识库文件，重新执行初始化命令即可更新向量库。

## 常见问题

### 1. 启动时报 `DASHSCOPE_API_KEY` 相关错误

请确认已经完成以下任一配置：

```bash
cp .env.example .env
```

并在 `.env` 中填入真实 key；或者在当前终端执行：

```bash
export DASHSCOPE_API_KEY="your-dashscope-api-key"
```

### 2. 问答没有检索到知识库内容

请先初始化知识库：

```bash
python scripts/init_knowledge_base.py
```

初始化完成后，项目根目录会生成 `chroma_db/` 和 `md5.txt`。

### 3. 修改知识库文件后没有生效

当前版本通过文件 MD5 去重。如果需要完整重建索引，可以删除本地生成文件后重新初始化：

```bash
rm -rf chroma_db md5.txt
python scripts/init_knowledge_base.py
```

## 示例问题

```text
扫地机器人无法正常回充，该怎么排查？
```

```text
家里有宠物，应该怎么维护主刷和滤网？
```

```text
小户型适合买哪类扫拖一体机器人？
```

```text
帮我生成本月机器人使用报告，并给出保养建议。
```

## 项目结构

```text
smart-hardware-rag-agent/
├── agent/
│   ├── react_agent.py
│   └── tools/
│       ├── agent_tools.py
│       └── middleware.py
├── rag/
│   ├── vector_store.py
│   └── rag_service.py
├── model/
│   └── factory.py
├── config/
│   ├── agent.yml
│   ├── chroma.yml
│   ├── prompts.yml
│   └── rag.yml
├── prompts/
│   ├── main_prompt.txt
│   ├── rag_summarize.txt
│   └── report_prompt.txt
├── utils/
│   ├── config_handler.py
│   ├── file_handler.py
│   ├── logger_handler.py
│   ├── path_tool.py
│   └── prompt_loader.py
├── data/
│   └── external/
├── scripts/
│   └── init_knowledge_base.py
├── tests/
│   └── test_demo_readiness.py
├── assets/
├── app.py
├── requirements.txt
└── README.md
```

## 配置说明

| 文件 | 说明 |
|---|---|
| `config/rag.yml` | 对话模型与 Embedding 模型配置 |
| `config/chroma.yml` | 向量库名称、持久化路径、分块参数、检索 Top-K |
| `config/prompts.yml` | 普通问答、RAG 总结、报告生成提示词路径 |
| `config/agent.yml` | 外部数据路径等 Agent 业务配置 |

## 已完成的优化

当前版本在基础 Agentic RAG 能力之上，已完成以下增强：

- **✅ 在线部署**：支持 Streamlit Cloud 一键部署，用户体验零门槛
- **✅ 真实数据接入**：将原 random mock 工具替换为真实接口——天气走 Open-Meteo API、用户位置走 IP 定位、用户身份/月份走会话级上下文，让 demo 贴近真实产品逻辑。
- **✅ 会话级用户上下文**：新增 `utils/session_context.py`，前端侧边栏可切换登录用户，Agent 调用 `get_user_id`/`get_user_location` 时读取的是当前会话绑定用户，而非随机值。
- **✅ 引用溯源**：RAG 答案末尾自动标注命中的知识库文档来源，提升售后场景下用户对 AI 回答的信任度。
- **✅ 数据生成器**：`scripts/generate_records.py` 可脚本化生成用户使用记录，支持扩展用户数与月份范围。
- **✅ 评测体系**：`eval/` 下提供 20 题评测集与评测脚本，支持分块策略、Top-K、Prompt 等维度的前后对比，量化优化效果。
- **✅ 知识库管理**：支持 MD5 去重、PDF/TXT 文档加载、分块策略配置

后续仍可继续增强：多轮对话记忆、知识库文档管理页面（上传/删除/重建索引）、更细粒度的 badcase 记录。

## 评测

```bash
# 优化前评测（修改分块参数/Prompt 前先跑一次）
python eval/run_eval.py --tag before

# 调整 chunk_size / k / prompt 后再跑一次
python eval/run_eval.py --tag after

# 对比前后效果，产出简历量化数字
python eval/compare.py before after
```
