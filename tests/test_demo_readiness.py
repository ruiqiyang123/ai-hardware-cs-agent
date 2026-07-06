import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class DemoReadinessTest(unittest.TestCase):
    def test_agent_uses_langgraph_prebuilt_api_available_in_requirements(self):
        react_agent = read_text("agent/react_agent.py")
        middleware = read_text("agent/tools/middleware.py")

        self.assertIn("from langgraph.prebuilt import create_react_agent", react_agent)
        self.assertNotIn("from langchain.agents import create_agent", react_agent)
        self.assertNotIn("langchain.agents.middleware", middleware)

    def test_runtime_dependencies_are_declared(self):
        requirements = read_text("requirements.txt")

        self.assertIn("langchain==0.3.30", requirements)
        self.assertIn("langgraph-prebuilt==0.6.5", requirements)
        self.assertIn("langchain-openai==0.3.35", requirements)
        self.assertIn("socksio==1.0.0", requirements)
        self.assertIn("python-dotenv", requirements)
        self.assertIn("posthog<6.0.0", requirements)

    def test_python39_compatible_type_annotations(self):
        model_factory = read_text("model/factory.py")

        self.assertIn("Union[Embeddings, BaseChatModel]", model_factory)
        self.assertNotIn("Embeddings | BaseChatModel", model_factory)

    def test_runtime_environment_overrides_local_dotenv(self):
        model_factory = read_text("model/factory.py")

        self.assertIn("load_dotenv(override=False)", model_factory)

    def test_streamlit_demo_is_fixed_to_mimo(self):
        app = read_text("app.py")

        self.assertIn('selected_provider = "mimo"', app)
        self.assertNotIn('st.radio(\n        "聊天模型"', app)
        self.assertNotIn("阿里云 DashScope", app)
        self.assertNotIn("MiMo API Key", app)
        self.assertNotIn("MiMo Base URL", app)
        self.assertNotIn("如何获取 API Key", app)
        self.assertIn("访客无需配置", app)

    def test_init_script_and_env_example_exist(self):
        self.assertTrue((ROOT / "scripts/init_knowledge_base.py").exists())

        env_example = read_text(".env.example")
        self.assertIn("DASHSCOPE_API_KEY=", env_example)
        self.assertIn("MIMO_API_KEY=", env_example)
        self.assertIn("MIMO_BASE_URL=", env_example)
        self.assertIn("MIMO_CHAT_MODEL=mimo-v2.5-pro", env_example)
        self.assertIn("CHAT_PROVIDER=mimo", env_example)
        self.assertIn("EMBEDDING_PROVIDER=", env_example)
        self.assertTrue((ROOT / "model/local_embeddings.py").exists())

    def test_readme_has_external_runbook(self):
        readme = read_text("README.md")

        # 仓库已重命名为 ai-hardware-cs-agent，README 同步更新
        self.assertIn("git clone https://github.com/ruiqiyang123/ai-hardware-cs-agent.git", readme)
        self.assertIn("pip install -r requirements.txt", readme)
        self.assertIn("python scripts/init_knowledge_base.py", readme)
        self.assertIn("streamlit run app.py", readme)
        # 在线 / 本地两种体验路径
        self.assertIn("在线体验", readme)
        self.assertIn("本地启动", readme)

    def test_root_license_file_is_not_exposed(self):
        self.assertFalse((ROOT / "LICENSE").exists())


if __name__ == "__main__":
    unittest.main()
