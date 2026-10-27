import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import lint


SCRIPT = Path(__file__).with_name("lint.py")
FIXTURE = Path(__file__).with_name("fixtures") / "ai-smelly.md"


class ProseCharacterCountTests(unittest.TestCase):
    def prose_count(self, text):
        _, stats = lint.run_lint(text, genre="tech")
        self.assertIn("prose_char_count", stats)
        return stats["prose_char_count"]

    def test_ignores_whitespace(self):
        self.assertEqual(self.prose_count("説明。\n\n   条件です。\t"), len("説明。条件です。"))

    def test_ignores_masked_markdown(self):
        prose = "設定を保存すると、次回の起動から適用されます。"
        additions = (
            "\n```cpp\n" + "int value = 0;\n" * 1000 + "```\n",
            "\n> 引用された説明です。\n",
            "\n| 項目 | 値 |\n|---|---|\n| 設定 | 有効 |\n",
            "\n- 設定を確認します。\n",
            "\n## 設定の確認\n",
            "\n<!-- 編集用のメモです。 -->\n",
            "\n`configuration.value`\n",
            "\n\n \t \n",
        )
        expected = self.prose_count(prose)
        for addition in additions:
            with self.subTest(addition=addition[:40]):
                self.assertEqual(self.prose_count(prose + addition), expected)

    def test_code_addition_preserves_findings_and_scoring_denominator(self):
        prose = FIXTURE.read_text(encoding="utf-8")
        findings, stats = lint.run_lint(prose, genre="tech")
        expanded = prose + "\n```cpp\n" + "int value = 0;\n" * 1500 + "```\n"
        expanded_findings, expanded_stats = lint.run_lint(expanded, genre="tech")
        self.assertEqual([f.to_dict() for f in findings],
                         [f.to_dict() for f in expanded_findings])
        self.assertIn("prose_char_count", stats)
        self.assertIn("prose_char_count", expanded_stats)
        self.assertEqual(stats["prose_char_count"], expanded_stats["prose_char_count"])

    def test_empty_and_short_prose_do_not_reach_scoring_threshold(self):
        for text, count in (("```text\n" + "x" * 1000 + "\n```", 0),
                            ("説" * 99 + "\n" * 1000, 99),
                            ("説" * 100, 100)):
            with self.subTest(count=count):
                self.assertEqual(self.prose_count(text), count)


class BaselineEncodingTests(unittest.TestCase):
    def run_with_baseline(self, baseline_text, encoding):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            baseline.write_text(baseline_text, encoding=encoding)
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(FIXTURE), "--genre", "tech",
                 "--json", "--baseline", str(baseline)],
                capture_output=True, text=True, encoding="utf-8",
            )

    def test_accepts_utf8_with_or_without_bom(self):
        for encoding in ("utf-8", "utf-8-sig"):
            with self.subTest(encoding=encoding):
                result = self.run_with_baseline('{"findings": []}', encoding)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                output = json.loads(result.stdout)
                self.assertEqual(output["baseline"]["summary"]["resolved"], 0)
                self.assertEqual(output["baseline"]["summary"]["persisting"], 0)
                self.assertEqual(output["baseline"]["summary"]["new"],
                                 output["stats"]["total_findings"])

    def test_invalid_json_remains_an_error(self):
        result = self.run_with_baseline("{", "utf-8-sig")
        self.assertEqual(result.returncode, 1)
        self.assertIn("--baseline", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
