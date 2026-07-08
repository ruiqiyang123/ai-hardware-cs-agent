<div align="center">

# KeyGuard AI Hardware Wallet CS Agent

**面向硬件钱包设备售后与安全自助服务的 Agentic RAG 智能客服 Demo**

用 LangGraph ReAct Agent、LangChain 工具链、Chroma RAG 和 Streamlit，构建一个可本地体验的智能硬件客服应用。

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-green)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6-orange)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-red)](https://streamlit.io/)

[在线体验](https://ai-hardware-cs-agent.streamlit.app/) · [部署说明](./DEPLOYMENT.md)

</div>

---

## 项目定位

这是一个面向硬件钱包设备售后与安全自助服务的 Agentic RAG 智能客服 Demo。项目使用虚构品牌 **KeyGuard**，模拟用户在硬件钱包开不了机、USB/蓝牙连接失败、App 识别不到设备、屏幕/按键异常、固件升级/恢复模式、设备丢失损坏和备份恢复中的咨询流程。

项目重点展示一个智能硬件客服应用从用户问题、Agent 决策、工具调用、知识库检索到最终回答生成的完整链路：

| 能力 | 当前实现 |
|------|----------|
| Agent 决策 | LangGraph `create_react_agent`，模型根据用户意图自主选择工具 |
| RAG 问答 | 官方/标准资料支撑的硬件钱包 TXT 知识库入库、分块、Embedding、Chroma 检索、答案引用溯源 |
| 工具调用 | 模拟链状态、用户地区、用户 ID、用户档案、当前月份、CSV 使用记录、报告模式切换 |
| 安全边界 | Prompt 强制禁止索要、保存或复述助记词、私钥、PIN、Passphrase |
| 动态 Prompt | 普通客服问答和月度安全报告使用不同系统提示词 |
| 会话上下文 | 侧边栏切换测试用户后，Agent 读取稳定的用户 ID、地区和档案 |
| 记忆压缩 | 超过 6 轮对话后压缩旧消息，保留最近上下文 |
| 评测闭环 | 30 题硬件钱包评测集、运行脚本、前后对比脚本、趋势记录脚本 |
| 工程验证 | pytest 测试覆盖 RAG、工具、配置、错误提示、事件流等模块 |

## RAG 数据来源

`data/` 下的知识库采用 **source-backed 改写**：事实来源参考官方支持文档、协议标准和生态文档，内容重新组织为 KeyGuard 客服条目，不复制官方原文，也不声称 KeyGuard 是任何真实品牌的官方项目。

每个 TXT 文件顶部都保留来源元数据，每条客服条目也带有 `来源参考：Sx`。加载知识库时，`txt_loader` 会把 TXT 拆成条目级 `Document`，并写入 `entry_id`、`entry_question`、`source_ids`、`source_urls` 等 metadata。最终回答展示命中的文件和条目标题；官方/标准 URL 保留在 metadata 中，默认不在主回答里展开。

当前知识库文件：

| 文件 | 覆盖内容 |
|------|----------|
| `data/故障排除.txt` | 16 条：开不了机、屏幕无显示、USB/蓝牙连接失败、App 识别不到、PIN 锁定、设备真伪/认证、设备丢失损坏 |
| `data/固件升级.txt` | 14 条：升级前检查、升级中断、恢复/bootloader 模式、修复流程、固件真实性、旧设备兼容、盲签设置边界 |
| `data/安全使用指南.txt` | 14 条：助记词/PIN/Passphrase 安全、设备屏幕核对、钓鱼风险、远程控制风险、假 App、无限授权风险 |
| `data/助记词与备份.txt` | 14 条：设备损坏后的恢复、BIP39/BIP44 解释、Passphrase、派生路径、恢复后余额为零、备份验证 |
| `data/交易与链网络.txt` | 14 条：硬件签名与链上确认边界、pending、RBF、nonce、盲签、授权撤销、WalletConnect、地址格式 |

这些文件统一采用“适用场景、排查步骤/建议动作、安全边界”的客服知识条目结构，当前共 **72 条 source-backed 客服条目**，便于 RAG 召回后生成可执行且边界清晰的答复。

代表性事实参考包括：

| 方向 | 参考来源 |
|------|----------|
| USB/设备识别 | [Ledger USB connection issues](https://support.ledger.com/article/115005165269-zd)、[Trezor Suite doesn't see my device](https://trezor.io/support/troubleshooting/device-issues/trezor-suite-doesn-t-see-my-device) |
| 蓝牙连接 | [Ledger Bluetooth setup](https://support.ledger.com/article/360019138694-zd)、[Ledger Bluetooth pairing issues](https://support.ledger.com/article/360025864773-zd) |
| 固件/修复 | [Ledger OS update guide](https://support.ledger.com/article/360013349800-zd)、[Trezor firmware update issues](https://trezor.io/support/troubleshooting/device-issues/firmware-update-issues) |
| 备份/恢复 | [BIP39](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)、[Trezor wallet backups](https://trezor.io/learn/security-privacy/personal-security-standards/understanding-trezor-wallet-backups-12-20-or-24-words) |
| Passphrase / 派生路径 | [Ledger Passphrase](https://www.ledger.com/academy/passphrase-an-advanced-security-feature)、[Trezor hidden wallets](https://trezor.io/support/troubleshooting/trezor-suite-issues/passphrase-hidden-wallets-issues)、[BIP44](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki) |
| 交易和授权边界 | [Ethereum gas docs](https://ethereum.org/developers/docs/gas/)、[Bitcoin Core RBF FAQ](https://bitcoincore.org/en/faq/optin_rbf/)、[WalletConnect Wallet SDK](https://docs.walletconnect.network/wallet-sdk/overview)、[Ledger revoke approvals](https://support.ledger.com/article/8700644160925-zd) |

## 在线体验

地址：[https://ai-hardware-cs-agent.streamlit.app/](https://ai-hardware-cs-agent.streamlit.app/)

当前线上 Demo 使用：

- **Chat 模型：** MiMo `mimo-v2.5-pro`
- **Embedding：** 本地 1024 维 Hash Embedding
- **向量库：** Chroma，本地持久化目录 `chroma_db/`
- **前端：** Streamlit Chat UI

本地 Hash Embedding 用于降低 Demo 运行门槛，保证没有额外 Embedding Key 时也能跑通；它不是生产级语义检索方案。真实客服系统应替换为具备语义理解能力的 Embedding 模型，并重新初始化 `chroma_db/`。

建议测试这几个问题：

| 场景 | 示例问题 | 可观察点 |
|------|----------|----------|
| 开机/供电 | 硬件钱包开不了机怎么办？ | Agent 调用 RAG，按电源、线缆、端口、售后检测逐步排查 |
| 蓝牙连接 | 蓝牙没法连接手机怎么办？ | 命中蓝牙配对、权限、旧配对记录、固件/App 版本排查 |
| USB 识别 | 电脑识别不到设备，怎么排查？ | 区分充电线、数据线、直连电脑、驱动/桥接组件和交叉测试 |
| 固件修复 | 固件升级中断了怎么办？ | 给出官方修复/恢复模式路径和敏感信息安全边界 |
| 设备丢失/损坏 | 设备丢了或坏了，资产还能恢复吗？ | 解释资产由助记词/Passphrase 恢复，提醒转移资产、重置旧设备和售后检测边界 |
| Passphrase / 隐藏钱包 | Passphrase 忘了，为什么恢复后余额为零？ | 区分助记词、Passphrase 和派生路径，明确客服不能找回或索要敏感信息 |
| 月度报告 | 帮我生成本月安全使用报告。 | 按用户 ID、月份、CSV 使用记录生成报告 |
| 记忆压缩 | 切换到 `1005 - 赵先生（成都）` | 预置多轮历史，用于演示对话压缩 |

## 系统架构

```text
用户问题
  -> Streamlit Chat UI
  -> 会话上下文：用户 ID / 地区 / 用户档案 / 历史对话
  -> ReactAgent
     -> LangGraph ReAct Agent
     -> 动态系统 Prompt
     -> 消息压缩
  -> 工具调用
     -> rag_summarize：Chroma RAG + LLM 总结 + 引用来源
     -> get_chain_status：模拟链网络状态、手续费和确认时间
     -> get_user_location：会话地区，IP 定位兜底
     -> get_user_id：当前测试用户 ID
     -> get_user_profile：SQLite 用户档案
     -> get_current_month：系统当前月份
     -> fetch_external_data：CSV 使用记录
     -> fill_context_for_report：报告模式切换信号
  -> MiMo 模型整合工具结果
  -> 输出安全客服答复或月度报告
```

## RAG 流程

```text
data/ 下带来源元数据的 TXT 文件
  -> txt_loader 条目级解析：entry_id / entry_question / source_ids / source_urls
  -> RecursiveCharacterTextSplitter（较大 chunk，尽量保留完整客服条目）
  -> Embedding 向量化
  -> Chroma 持久化
  -> 用户提问时 Top-K 检索
  -> 关键词兜底召回
  -> rag_summarize Prompt
  -> LLM 基于参考资料生成答案
  -> 追加“参考来源：xxx.txt 第 N 条「条目标题」”
```

当前 Chroma 配置见 [config/chroma.yml](./config/chroma.yml)：

- `chunk_size: 700`
- `chunk_overlap: 80`
- `k: 3`
- 支持文件类型：`txt`、`pdf`

## 代码导览

| 文件 / 目录 | 作用 |
|-------------|------|
| [app.py](./app.py) | Streamlit 入口，负责页面、测试用户、模型配置、聊天渲染和状态展示 |
| [agent/react_agent.py](./agent/react_agent.py) | 封装 LangGraph ReAct Agent，输出 `thought`、`tool_call`、`tool_result`、`answer` 四类事件 |
| [agent/tools/agent_tools.py](./agent/tools/agent_tools.py) | Agent 工具声明层，包含 RAG、链状态、用户 ID、报告数据等工具 |
| [agent/tools/profile_tools.py](./agent/tools/profile_tools.py) | 用户档案工具，让 Agent 获取经验等级、设备型号、常用链、连接方式和备份状态 |
| [agent/services/chain_status_service.py](./agent/services/chain_status_service.py) | 模拟链网络状态服务 |
| [agent/services/usage_records.py](./agent/services/usage_records.py) | CSV 使用记录读取、解析和月份兜底 |
| [rag/rag_service.py](./rag/rag_service.py) | RAG 总结主链路，负责检索、关键词兜底、LLM 总结和来源拼接 |
| [rag/vector_store.py](./rag/vector_store.py) | Chroma 向量库、文档加载、MD5 去重和文本分块 |
| [rag/keyword_fallback.py](./rag/keyword_fallback.py) | 高频硬件钱包问题的关键词兜底召回 |
| [database/profile_db.py](./database/profile_db.py) | SQLite 用户档案存储 |
| [eval/](./eval) | 30 题评测集、运行脚本、对比脚本和趋势脚本 |
| [tests/](./tests) | pytest 单元测试 |

## 工具列表

| 工具 | 触发场景 | 数据来源 |
|------|----------|----------|
| `rag_summarize` | 连接、备份、固件、安全、交易知识问答 | `data/` 知识库 + Chroma |
| `get_chain_status` | 已签名交易 pending、手续费、链网络状态边界说明 | 模拟链状态数据，不代表实时费率 |
| `get_user_location` | 需要当前用户地区 | Streamlit 会话上下文，IP 定位兜底 |
| `get_user_id` | 需要当前登录用户 | Streamlit 侧边栏选择 |
| `get_user_profile` | 个性化安全建议 | SQLite 用户档案 |
| `get_current_month` | 生成本月报告 | 系统当前时间 |
| `fetch_external_data` | 生成安全使用报告 | `data/external/records.csv` |
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
rm -rf chroma_db md5.txt
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
- 硬件钱包前端场景是否就绪
- RAG 来源提取和关键词兜底
- 链状态服务解析
- CSV 使用记录解析
- 会话上下文稳定性
- LangGraph 事件流兼容
- Prompt 安全边界和 RAG 调用约束

### RAG / Agent 效果评测

```bash
python eval/run_eval.py --tag wallet-local --record
python eval/trend.py
```

评测集位于 [eval/eval_cases.json](./eval/eval_cases.json)，目前包含 30 道题，主覆盖开机/供电、USB/蓝牙连接、屏幕/按键、PIN 锁定、固件恢复、设备丢失损坏、备份恢复和硬件签名边界。

最近一次本地真实 Agent 评测：

```bash
python eval/run_eval.py --tag wallet-rag-v2 --record
```

结果已保存到 [eval/eval_results/wallet-rag-v2.json](./eval/eval_results/wallet-rag-v2.json)，并追加到 `eval/eval_results/history.jsonl`。

| 指标 | 结果 |
|------|------|
| 评测题数 | 30 |
| 整体关键词覆盖率 | 83.3% |
| 高分分类 | 硬件签名边界 100%、固件修复 97.1%、蓝牙连接 93.3%、开机与供电 90.0%、设备丢失损坏 90.0% |
| 待优化分类 | USB 连接 46.7%、安全报告 60.0%、安全边界 70.0% |

当前 badcase 主要来自关键词评分的严格匹配和少数回答压缩：例如“USB-C / 数据线 / USB Hub”“不要复述”等词在回答中有同义表达但未命中。后续可通过更细的硬件连接专项评测和语义评分替代纯关键词评分。
