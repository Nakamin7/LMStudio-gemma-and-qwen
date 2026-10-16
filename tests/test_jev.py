import json
import os
import unittest
from unittest.mock import patch

from src import jev
from src import providers, tools


class JevUnitTests(unittest.TestCase):
    def test_payload_limits_and_noul_result(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self):
                return json.dumps({"answers": {"relevant": {"type": "noul", "noul": 0.91}}}).encode()

        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-key"}, clear=False), \
             patch("src.jev.urlopen", return_value=FakeResponse()) as open_mock:
            result = jev.relevance_probability("q" * 2500, "s" * 300, "c" * 1800)
        self.assertEqual(result, 0.91)
        payload = json.loads(open_mock.call_args.args[0].data.decode())
        self.assertLessEqual(len(payload["state"]["question"]), 2000)
        self.assertLessEqual(len(payload["state"]["candidate_source"]), 160)
        self.assertLessEqual(len(payload["state"]["candidate_passage"]), 1200)
        self.assertNotIn("tools", payload)
        self.assertEqual(payload["model"], "jev-1.13.0")

    def test_missing_key_fails_closed(self):
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": ""}, clear=False):
            with self.assertRaises(jev.JevError):
                jev.relevance_probability("question", "doc.md", "text")

    def test_enabled_requires_consent(self):
        with self.assertRaises(ValueError):
            providers.set_jev_preferences(True, False)

    def test_local_search_does_not_call_jev_when_disabled(self):
        result = [{"source": "a.md", "content": "some relevant text"}]
        with patch("src.tools.search_documents", return_value=result), \
             patch("src.tools.jev_preferences", return_value=(False, False)), \
             patch("src.jev.relevance_probability") as judge:
            text = tools.search_knowledge_base("question")
        judge.assert_not_called()
        self.assertIn("a.md", text)

    def test_jev_failure_falls_back_to_local_results(self):
        result = [{"source": "a.md", "content": "some relevant text"}]
        with patch("src.tools.search_documents", return_value=result), \
             patch("src.tools.jev_preferences", return_value=(True, True)), \
             patch("src.jev.relevance_probability", side_effect=jev.JevError("unavailable")):
            text = tools.search_knowledge_base("question")
        self.assertIn("ローカル検索結果を表示します", text)
        self.assertIn("a.md", text)


if __name__ == "__main__":
    unittest.main()
