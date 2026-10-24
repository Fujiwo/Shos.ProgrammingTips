"""Articles/ 配下の記事から、プログラミング言語ごとの目次 Articles/README.md を生成する。

- Claude Code の PostToolUse フック (Edit|Write) から呼ばれる。標準入力の JSON の
  tool_input.file_path が Articles/ の下の記事 (*.md) のときだけ生成する。
- 引数 --force を付けて手動で実行すると、入力によらず生成する。
- 記事のタイトルは、記事の最初の H1 見出し (# ...) から取る。
"""

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ARTICLES_ROOT = REPOSITORY_ROOT / "Articles"
TOC_PATH = ARTICLES_ROOT / "README.md"

# フォルダー名と、目次に表示する言語名。ここにないフォルダーは、フォルダー名のまま末尾に並べる
LANGUAGES = {
    "CSharp": "C#",
    "CPlusplus": "C++",
    "JavaScript": "JavaScript",
}
# 記事ではないファイルを置くフォルダー
NON_ARTICLE_DIRECTORY_NAMES = {"Sources", "Images"}

HEADER = """<!-- このファイルは .claude/hooks/update_articles_toc.py が自動生成する。直接編集しないこと。 -->

# 目次

プログラミング言語ごとの記事の一覧です。
"""
NO_ARTICLES = "(記事はまだありません)"


def is_article(path):
    relative_parts = path.relative_to(ARTICLES_ROOT).parts
    return (path.suffix.lower() == ".md" and path != TOC_PATH and len(relative_parts) >= 2
            and not NON_ARTICLE_DIRECTORY_NAMES.intersection(relative_parts))


def is_article_edited(hook_input):
    file_path = hook_input.get("tool_input", {}).get("file_path")
    if not file_path:
        return False
    path = Path(file_path).resolve()
    return path.is_relative_to(ARTICLES_ROOT) and is_article(path)


def read_title(article_path):
    # コードブロックの中の "# " (シェルのコメントなど) は見出しとして扱わない
    in_code_block = False
    for line in article_path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_code_block = not in_code_block
        elif not in_code_block and line.startswith("# "):
            return line[2:].strip()
    return article_path.stem


def escape_link_text(text):
    return text.replace("[", r"\[").replace("]", r"\]")


def language_directories():
    # LANGUAGES の言語は、フォルダーがなくても (Git は空のフォルダーを管理しない) 節を出す
    existing = {path.name: path for path in ARTICLES_ROOT.iterdir() if path.is_dir()}
    known = [existing.get(name, ARTICLES_ROOT / name) for name in LANGUAGES]
    unknown = sorted(path for name, path in existing.items() if name not in LANGUAGES)
    return known + unknown


def build_language_section(language_directory):
    articles = (sorted(path for path in language_directory.rglob("*.md") if is_article(path))
                if language_directory.exists() else [])
    lines = [f"## {LANGUAGES.get(language_directory.name, language_directory.name)}", ""]
    if not articles:
        lines.append(NO_ARTICLES)
    for article in articles:
        link = article.relative_to(ARTICLES_ROOT).as_posix().replace(" ", "%20")
        lines.append(f"- [{escape_link_text(read_title(article))}]({link})")
    return "\n".join(lines) + "\n"


def build_toc():
    sections = [build_language_section(directory) for directory in language_directories()]
    return HEADER + "\n" + "\n".join(sections)


def main():
    if "--force" not in sys.argv:
        try:
            hook_input = json.load(sys.stdin)
        except json.JSONDecodeError:
            return 0
        if not is_article_edited(hook_input):
            return 0
    TOC_PATH.write_text(build_toc(), encoding="utf-8", newline="")
    print(f"{TOC_PATH.relative_to(REPOSITORY_ROOT)} を更新した")
    return 0


if __name__ == "__main__":
    sys.exit(main())
