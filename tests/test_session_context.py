import unittest

from utils import session_context


class SessionContextTest(unittest.TestCase):
    def tearDown(self):
        session_context.reset()

    def test_user_id_and_location_are_stable_after_setting(self):
        session_context.set_user_id("1004")
        session_context.set_location("北京")

        self.assertEqual(session_context.current_user_id(), "1004")
        self.assertEqual(session_context.current_location(), "北京")

    def test_reset_restores_demo_defaults(self):
        session_context.set_user_id("1002")
        session_context.set_location("合肥")

        session_context.reset()

        self.assertEqual(session_context.current_user_id(), "1001")
        self.assertIsNone(session_context.current_location())


if __name__ == "__main__":
    unittest.main()
