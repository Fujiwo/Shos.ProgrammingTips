""".claude/skills の内容を .github/skills に同期する (.claude/skills が正)。

- Claude Code の PostToolUse フック (Edit|Write) から呼ばれる。標準入力の JSON の
  tool_input.file_path が .claude/skills の下のときだけ同期する。
- 引数 --force を付けて手動で実行すると、入力によらず同期する。
- 同期は全体のミラーリングで行う。.claude/skills にないファイルは .github/skills から消す。
"""

import filecmp
import json
import shutil
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / ".claude" / "skills"
TARGET_ROOT = REPOSITORY_ROOT / ".github" / "skills"
# Claude Code の作業用フォルダーと Python のキャッシュは同期しない
EXCLUDED_DIRECTORY_NAMES = {".claude", "__pycache__"}


def is_source_edited(hook_input):
    file_path = hook_input.get("tool_input", {}).get("file_path")
    if not file_path:
        return False
    return Path(file_path).resolve().is_relative_to(SOURCE_ROOT)


def is_excluded(relative_path):
    return any(part in EXCLUDED_DIRECTORY_NAMES for part in relative_path.parts)


def relative_files(root):
    relative_paths = (path.relative_to(root) for path in root.rglob("*") if path.is_file())
    return {relative_path for relative_path in relative_paths if not is_excluded(relative_path)}


def remove_empty_directories(root):
    directories = (path for path in root.rglob("*")
                   if path.is_dir() and not is_excluded(path.relative_to(root)))
    for directory in sorted(directories, reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()


def mirror():
    source_files = relative_files(SOURCE_ROOT)
    target_files = relative_files(TARGET_ROOT) if TARGET_ROOT.exists() else set()

    copied = 0
    for relative_path in sorted(source_files):
        source_path = SOURCE_ROOT / relative_path
        target_path = TARGET_ROOT / relative_path
        if target_path.exists() and filecmp.cmp(source_path, target_path, shallow=False):
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        copied += 1

    removed = target_files - source_files
    for relative_path in removed:
        (TARGET_ROOT / relative_path).unlink()
    remove_empty_directories(TARGET_ROOT)
    return copied, len(removed)


def main():
    if "--force" not in sys.argv:
        try:
            hook_input = json.load(sys.stdin)
        except json.JSONDecodeError:
            return 0
        if not is_source_edited(hook_input):
            return 0
    copied, removed = mirror()
    print(f".github/skills を .claude/skills に同期した (更新 {copied} 件、削除 {removed} 件)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
