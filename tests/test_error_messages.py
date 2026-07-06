import unittest

from utils.error_messages import format_agent_error


class ErrorMessagesTest(unittest.TestCase):
    def test_format_agent_error_hides_raw_model_exception(self):
        message = format_agent_error(ValueError("dashscope error: insufficient quota for api key sk-secret"))

        self.assertIn("模型服务暂时不可用", message)
        self.assertIn("共享额度", message)
        self.assertNotIn("sk-secret", message)

    def test_format_agent_error_handles_invalid_key(self):
        message = format_agent_error(ValueError("Invalid API-key provided"))

        self.assertIn("API Key", message)
        self.assertIn("侧边栏", message)


if __name__ == "__main__":
    unittest.main()
