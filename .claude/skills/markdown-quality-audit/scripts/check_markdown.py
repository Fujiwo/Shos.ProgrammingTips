"""Markdown を機械的に検査する。

常に行う検査:
- Blocking : 相対リンク・画像のリンク切れ、閉じていないコードフェンス
- Minor    : 長すぎるコードブロック (--max-code-lines、既定 60 行)

オプションで有効にする検査 (プロジェクトの書式ルールに合わせて指定する):
- Important: コードフェンス直前の言語ラベルの欠落 (--language-label-pattern)
- Important: Mermaid の使用 (--forbid-mermaid)
- Minor    : Markdown の脚注記法 (--forbid-footnotes)

使い方: python check_markdown.py 対象 [対象 ...] [オプション]
対象は Markdown ファイルまたはフォルダー (フォルダーは配下の *.md を再帰的に検査する)。
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

DEFAULT_MAX_CODE_BLOCK_LINES = 60

FENCE_PATTERN = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
INLINE_CODE_PATTERN = re.compile(r"`[^`]*`")
FOOTNOTE_PATTERN = re.compile(r"\[\^[^\]]+\]")
EXTERNAL_LINK_PREFIXES = ("http://", "https://", "mailto:", "#")

SEVERITIES = ("Blocking", "Important", "Minor")


@dataclass
class Finding:
    severity: str
    path: Path
    line_number: int
    message: str


@dataclass
class Rules:
    max_code_block_lines: int
    language_label_pattern: re.Pattern | None
    forbid_mermaid: bool
    forbid_footnotes: bool


def collect_markdown_files(targets):
    for target in targets:
        if target.is_dir():
            yield from sorted(target.rglob("*.md"))
        elif target.suffix.lower() == ".md":
            yield target


def is_broken_link(markdown_path, link):
    if link.startswith(EXTERNAL_LINK_PREFIXES):
        return False
    local_part = unquote(link.split("#", 1)[0])
    return not (markdown_path.parent / local_part).exists()


def check_text_line(markdown_path, line_number, line, rules):
    text = INLINE_CODE_PATTERN.sub("", line)
    for link in LINK_PATTERN.findall(text):
        if is_broken_link(markdown_path, link):
            yield Finding("Blocking", markdown_path, line_number, f"リンク切れ: {link}")
    if rules.forbid_footnotes and FOOTNOTE_PATTERN.search(text):
        yield Finding("Minor", markdown_path, line_number, "脚注記法 ([^1]) を使っている")


def previous_non_blank_line(lines, index):
    for previous in reversed(lines[:index]):
        if previous.strip():
            return previous
    return ""


def check_fence_opening(markdown_path, lines, index, info_string, rules):
    line_number = index + 1
    if rules.forbid_mermaid and info_string.strip().lower() == "mermaid":
        yield Finding("Important", markdown_path, line_number, "Mermaid を使っている")
    label_pattern = rules.language_label_pattern
    if label_pattern and not label_pattern.match(previous_non_blank_line(lines, index).strip()):
        yield Finding("Important", markdown_path, line_number, "コードブロックの直前に言語ラベルがない")


def is_closing_fence(fence_match, opening_fence):
    if not fence_match:
        return False
    fence = fence_match.group(1)
    return (fence[0] == opening_fence[0] and len(fence) >= len(opening_fence)
            and not fence_match.group(2).strip())


def check_file(markdown_path, rules):
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    open_fence = None  # (フェンス文字列, 開始行のインデックス)
    for index, line in enumerate(lines):
        fence_match = FENCE_PATTERN.match(line)
        if open_fence is None:
            if fence_match:
                open_fence = (fence_match.group(1), index)
                yield from check_fence_opening(markdown_path, lines, index, fence_match.group(2), rules)
            else:
                yield from check_text_line(markdown_path, index + 1, line, rules)
            continue
        fence, start_index = open_fence
        if is_closing_fence(fence_match, fence):
            code_lines = index - start_index - 1
            if code_lines > rules.max_code_block_lines:
                yield Finding("Minor", markdown_path, start_index + 1,
                              f"コードブロックが {code_lines} 行ある (目安 {rules.max_code_block_lines} 行以下)")
            open_fence = None
    if open_fence is not None:
        yield Finding("Blocking", markdown_path, open_fence[1] + 1, "コードフェンスが閉じていない")


def report(findings):
    for severity in SEVERITIES:
        matched = [finding for finding in findings if finding.severity == severity]
        print(f"## {severity} ({len(matched)})")
        for finding in matched:
            print(f"- {finding.path}:{finding.line_number}: {finding.message}")
        print()


def parse_arguments():
    parser = argparse.ArgumentParser(description="Markdown のリンク切れ・コードフェンスなどを検査する")
    parser.add_argument("targets", nargs="+", type=Path, help="検査する Markdown ファイルまたはフォルダー")
    parser.add_argument("--max-code-lines", type=int, default=DEFAULT_MAX_CODE_BLOCK_LINES,
                        help=f"コードブロックの行数の目安 (既定 {DEFAULT_MAX_CODE_BLOCK_LINES})")
    parser.add_argument("--language-label-pattern",
                        help="コードフェンスの直前の行が満たすべき正規表現 (例: '^_\\[.+\\]_$')")
    parser.add_argument("--forbid-mermaid", action="store_true", help="Mermaid のコードフェンスを所見にする")
    parser.add_argument("--forbid-footnotes", action="store_true", help="脚注記法 ([^1]) を所見にする")
    parser.add_argument("--fail-on-findings", action="store_true",
                        help="Blocking 以外の所見があっても終了コード 1 を返す")
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    missing = [target for target in arguments.targets if not target.exists()]
    if missing:
        print(f"対象が見つからない: {', '.join(map(str, missing))}", file=sys.stderr)
        return 2

    label_pattern = arguments.language_label_pattern
    rules = Rules(
        max_code_block_lines=arguments.max_code_lines,
        language_label_pattern=re.compile(label_pattern) if label_pattern else None,
        forbid_mermaid=arguments.forbid_mermaid,
        forbid_footnotes=arguments.forbid_footnotes,
    )
    markdown_files = list(collect_markdown_files(arguments.targets))
    findings = [finding for path in markdown_files for finding in check_file(path, rules)]
    print(f"検査したファイル: {len(markdown_files)}\n")
    report(findings)

    has_blocking = any(finding.severity == "Blocking" for finding in findings)
    return 1 if has_blocking or (arguments.fail_on_findings and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
