import unittest

from bulking_app.ai.factory import get_planner


class AIFactoryTests(unittest.TestCase):
    def test_unknown_provider_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "AI_PROVIDER"):
            get_planner("unknown")


if __name__ == "__main__":
    unittest.main()
