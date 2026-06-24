# 🚀 Streamlit Cloud 部署指南

本指南帮助你将 Smart Hardware RAG Agent 部署到 Streamlit Cloud，实现零门槛在线体验。

## 前置准备

1. **Streamlit Cloud 账号**：访问 [share.streamlit.io](https://share.streamlit.io/) 注册
2. **GitHub 仓库**：确保项目代码已推送到 GitHub
3. **API Key**：准备 DashScope 或 MiMo API Key

## 部署步骤

### 1. 确保 GitHub 仓库更新

```bash
git add .
git commit -m "feat: 添加 Streamlit Cloud 部署配置"
git push origin main
```

### 2. 登录 Streamlit Cloud

访问 [share.streamlit.io](https://share.streamlit.io/)，选择 "Sign in with GitHub"。

### 3. 创建新应用

1. 点击 "New app"
2. 选择你的 GitHub 仓库：`ruiqiyang123/smart-hardware-rag-agent`
3. 分支选择：`main`
4. Main file path：`app.py`
5. Python version：`3.11`

### 4. 配置环境变量（可选）

如果你希望部署后使用固定的 API Key，可以在 "Advanced settings" 中设置：

```bash
DASHSCOPE_API_KEY=your-api-key
CHAT_PROVIDER=dashscope
EMBEDDING_PROVIDER=dashscope
```

或者使用 MiMo：

```bash
MIMO_API_KEY=your-mimo-key
MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
MIMO_CHAT_MODEL=mimo-v2.5-pro
CHAT_PROVIDER=mimo
EMBEDDING_PROVIDER=local
```

**推荐做法**：不设置环境变量，让用户在侧边栏输入临时 API Key。

### 5. 点击 Deploy

等待几分钟后，应用即可部署成功。你会得到一个类似这样的 URL：

```
https://smart-hardware-rag-agent-xyz.streamlit.app
```

## 自动更新

每次你推送新代码到 GitHub，Streamlit Cloud 会自动重新部署最新版本。

## 常见问题

### Q: 部署后页面加载很慢？
A: 首次启动需要初始化知识库，之后访问速度会快很多。建议设置固定环境变量避免重复初始化。

### Q: 如何查看部署日志？
A: 在 Streamlit Cloud 控制台点击你的应用，选择 "Logs" 标签。

### Q: 部署失败怎么办？
A: 检查以下内容：
- Python 版本是否为 3.11
- `requirements.txt` 是否正确
- 环境变量格式是否正确

### Q: 如何保护 API Key？
A: 不要在代码中硬编码 API Key，使用 Streamlit Cloud 的环境变量功能。

## 技术支持

- Streamlit Cloud 文档：https://docs.streamlit.io/streamlit-cloud
- 本项目 Issues：https://github.com/ruiqiyang123/smart-hardware-rag-agent/issues