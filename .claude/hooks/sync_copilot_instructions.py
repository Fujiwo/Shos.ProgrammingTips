"""CLAUDE.md の内容を .github/copilot-instructions.md に同期する。

- Claude Code の PostToolUse フック (Edit|Write) から呼ばれる。標準入力の JSON の
  tool_input.file_path がリポジトリ直下の CLAUDE.md のときだけ同期する。
- 引数 --force を付けて手動で実行すると、入力によらず同期する。
"""

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPOSITORY_ROOT / "CLAUDE.md"
TARGET_PATH = REPOSITORY_ROOT / ".github" / "copilot-instructions.md"

GENERATED_NOTICE = (
    "<!-- このファイルは CLAUDE.md から自動生成される。"
    "直接編集せず、CLAUDE.md を編集すること。 -->\n\n"
)
SOURCE_TITLE = "# CLAUDE.md"
TARGET_TITLE = "# Copilot Instructions"


def is_source_edited(hook_input):
    file_path = hook_input.get("tool_input", {}).get("file_path")
    if not file_path:
        return False
    return Path(file_path).resolve() == SOURCE_PATH


def build_target_text(source_text):
    body = source_text.replace(SOURCE_TITLE, TARGET_TITLE, 1)
    return GENERATED_NOTICE + body


def sync():
    target_text = build_target_text(SOURCE_PATH.read_text(encoding="utf-8"))
    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    TARGET_PATH.write_text(target_text, encoding="utf-8", newline="")


def main():
    if "--force" not in sys.argv:
        try:
            hook_input = json.load(sys.stdin)
        except json.JSONDecodeError:
            return 0
        if not is_source_edited(hook_input):
            return 0
    sync()
    print(f"{TARGET_PATH.relative_to(REPOSITORY_ROOT)} を CLAUDE.md に同期した")
    return 0


if __name__ == "__main__":
    sys.exit(main())
