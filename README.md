<div align="center">

# Smart Hardware RAG Agent

**面向智能硬件售后的 Agentic RAG 客服系统**

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
&nbsp;
[![LangChain](https://img.shields.io/badge/LangChain-0.3-green)](https://www.langchain.com/)
&nbsp;
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-orange)](https://github.com/langchain-ai/langgraph)
&nbsp;
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-red)](https://streamlit.io/)

</div>

---

## 项目简介

Smart Hardware RAG Agent 是一个面向智能硬件售后场景的 AI Agent 应用项目。项目以扫地机器人/扫拖一体机的售后咨询为示例，围绕“用户提问 - 意图判断 - 工具调用 - 知识库检索 - 答案生成 - 使用报告输出”构建完整的 Agentic RAG 流程。

这个项目重点展示三类能力：

- 用 RAG 将产品知识、故障排查、维护保养、选购指南等非结构化资料接入问答流程。
- 用 ReAct Agent 根据用户意图自主选择工具，例如知识库检索、用户信息获取、外部数据查询和报告生成。
- 用中间件和提示词配置管理不同业务场景，让普通问答和个性化报告生成走不同的响应策略。

当前版本聚焦核心链路演示，后续会继续补充知识库管理、引用溯源、评测集和更稳定的产品化交互。

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
| 大模型 | Qwen / DashScope `ChatTongyi` |
| Embedding | DashScope `text-embedding-v4` |
| Agent 框架 | LangChain + LangGraph |
| 向量数据库 | Chroma |
| 文档处理 | PyPDF + LangChain Text Splitters |
| 前端 | Streamlit |
| 配置 | YAML |
| 数据模拟 | CSV |

## 快速开始

### 环境要求

- Python 3.10+
- DashScope API Key

### 克隆项目

```bash
git clone https://github.com/ruiqiyang123/smart-hardware-rag-agent.git
cd smart-hardware-rag-agent
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
export DASHSCOPE_API_KEY="your-api-key"
```

Windows CMD:

```bat
set DASHSCOPE_API_KEY=your-api-key
```

### 初始化知识库

```bash
python -c "from rag.vector_store import VectorStoreService; VectorStoreService().load_document()"
```

### 启动应用

```bash
streamlit run app.py
```

默认访问地址：

```text
http://localhost:8501
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

## 后续优化方向

当前版本已经具备基础 Agentic RAG 演示能力，后续计划重点增强以下内容：

- 升级并锁定 LangChain/LangGraph 依赖版本，提升环境可复现性。
- 将随机 mock 工具改为可配置的确定性数据接口。
- 增加知识库文档管理页面，支持上传、查看、删除和重建索引。
- 在答案中展示引用来源，方便用户追溯知识库片段。
- 增加 badcase 评测集，记录问题、期望答案、检索命中和工具调用结果。
- 优化 Streamlit 页面，让售后问答、知识库管理和报告生成流程更清晰。

## 简历项目关键词

`AI Agent` · `RAG` · `LangChain` · `LangGraph` · `Tool Calling` · `Prompt Engineering` · `Chroma` · `Streamlit` · `智能客服` · `智能硬件售后`
