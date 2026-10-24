"""記事に埋め込んだコードが、Sources/ の下のサンプルコードと一致するかを確認する。

- Articles/<言語>/ の下の記事 (*.md) から、コードブロックを取り出す。
- 言語 (フェンスの情報文字列) が SOURCE_EXTENSIONS にあるコードブロックだけを確認する。
  実行結果 (text) や疑似コードは確認しない。
- コードブロックの中身が、記事と同じフォルダーの Sources/ の下にある、対応する拡張子の
  いずれかのファイルにそのまま含まれていれば一致とする。BOM と改行コードの違いは無視する。
- 一致しないコードブロックがあれば、その場所を表示して終了コード 1 で終わる。
"""

import re
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ARTICLES_ROOT = REPOSITORY_ROOT / "Articles"

# フェンスの言語と、それに対応するソースファイルの拡張子
SOURCE_EXTENSIONS = {
    "cpp": {".cpp", ".h", ".hpp", ".ixx"},
    "csharp": {".cs"},
    "cs": {".cs"},
    "javascript": {".js", ".mjs", ".cjs"},
    "js": {".js", ".mjs", ".cjs"},
}
# ビルドの出力や依存パッケージのフォルダーは探さない
EXCLUDED_DIRECTORY_NAMES = {"bin", "obj", "node_modules", ".vs", "x64", "x86"}

CODE_BLOCK_PATTERN = re.compile(r"^```(\w+)[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)


def normalize(text):
    return text.lstrip("﻿").replace("\r\n", "\n")


def articles():
    return sorted(path for path in ARTICLES_ROOT.glob("*/*.md"))


def source_texts(sources_root, extensions):
    paths = (path for path in sources_root.rglob("*")
             if path.is_file() and path.suffix.lower() in extensions
             and not EXCLUDED_DIRECTORY_NAMES.intersection(path.relative_to(sources_root).parts))
    return [normalize(path.read_text(encoding="utf-8")) for path in paths]


def line_number(text, offset):
    return text.count("\n", 0, offset) + 1


def mismatched_blocks(article_path):
    text = normalize(article_path.read_text(encoding="utf-8"))
    sources_root = article_path.parent / "Sources"
    for match in CODE_BLOCK_PATTERN.finditer(text):
        extensions = SOURCE_EXTENSIONS.get(match.group(1).lower())
        if extensions is None:
            continue
        code = match.group(2).strip("\n")
        if not any(code in source for source in source_texts(sources_root, extensions)):
            yield line_number(text, match.start())


def main():
    mismatches = [(article, line) for article in articles() for line in mismatched_blocks(article)]
    for article, line in mismatches:
        print(f"{article.relative_to(REPOSITORY_ROOT).as_posix()}:{line}: "
              "コードブロックが Sources/ のコードと一致しない")
    print(f"確認した記事: {len(articles())}、一致しないコードブロック: {len(mismatches)}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
