import unittest

from bulking_app.ai.factory import get_planner


class AIFactoryTests(unittest.TestCase):
    def test_unknown_provider_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "AI_PROVIDER"):
            get_planner("unknown")

    def test_openai_is_no_longer_supported(self):
        with self.assertRaisesRegex(ValueError, "AI_PROVIDER"):
            get_planner("openai")

    def test_openai_sdk_is_not_a_dependency(self):
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        self.assertNotIn("openai", (root / "requirements.txt").read_text().lower())
        self.assertFalse((root / "bulking_app/ai/openai_adapter.py").exists())


if __name__ == "__main__":
    unittest.main()
