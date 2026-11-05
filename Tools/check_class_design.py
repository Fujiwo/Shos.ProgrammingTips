"""サンプルに、継承されると誤動作しうるクラス (バグ含みのコード) がないかを確認する。

規則は CLAUDE.md の「サンプルコード」。継承を想定しないクラスは、継承を禁じておく。

- C++ (Sources/ の下の .cpp・.h・.hpp・.ixx): クラス・構造体の定義に、final を付けるか、
  virtual デストラクター (派生クラスでは override のデストラクターでもよい) を宣言する。
  どちらもないと、継承されて基底クラスのポインター経由で破棄されたときに、
  派生クラスのデストラクターが呼ばれない。
- C# (Sources/ の下の .cs): class と record (record struct を除く) に、sealed・static・abstract の
  いずれかを付ける。継承されることを想定して virtual・abstract・protected のメンバーを
  宣言したクラスは対象外。C# のビルドでは、アナライザーの CA1852 も internal の型を検査する。

違反があれば、その場所を表示して終了コード 1 で終わる。

正規表現による簡易な検査なので、次の限界がある (残る危険)。
- 見逃す: マクロで生成したクラス、C++ の明示的特殊化 (class X<int> { ... }) や属性・alignas を
  付けたクラス、生文字列リテラル (C++ の R"(...)"、C# の \"\"\"...\"\"\") の中の波かっこで
  対応がずれた場合、C# の partial クラスのうち別ファイルの部分に付けた修飾子。
- 誤検知する: 基底クラスの virtual デストラクターを受け継ぐだけの C++ の派生クラス。
  final を付けるか、~T() override を宣言して避ける。
- 継承を禁じても、仮想関数を持つクラスをコピーしたときのスライシングなど、
  継承を許したクラスに残る危険は防げない。これはコードのコメントで残す (CLAUDE.md)。
"""

import re
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ARTICLES_ROOT = REPOSITORY_ROOT / "Articles"

# ビルドの出力や依存パッケージのフォルダーは探さない
EXCLUDED_DIRECTORY_NAMES = {"bin", "obj", "node_modules", ".vs", "x64", "x86"}

# コメントと、文字列・文字リテラル。数字の区切り (C++ の 1'000) は文字リテラルとみなさない
NON_CODE_PATTERN = re.compile(
    r"//[^\n]*|/\*.*?\*/|\"(?:\\.|[^\"\\\n])*\"|(?<![\w])'(?:\\.|[^'\\\n])*'",
    re.DOTALL)

# C++: class 名前 [final] [: 基底クラス] {
CPP_CLASS_HEAD_PATTERN = re.compile(r"\b(?:class|struct)\s+([A-Za-z_]\w*)(\s+final\b)?\s*(?::[^;{]*)?\{")
CPP_ENUM_BEFORE_PATTERN = re.compile(r"\benum\s*$")

# C#: [修飾子...] class|record [class] 名前
CSHARP_MODIFIERS = r"(?:public|internal|private|protected|file|sealed|static|abstract|partial|unsafe|new|readonly)"
CSHARP_CLASS_HEAD_PATTERN = re.compile(
    rf"((?:\b{CSHARP_MODIFIERS}\s+)*)\b(?:class|record(?!\s+struct\b)(?:\s+class)?)\s+([A-Za-z_]\w*)")
CSHARP_INHERITANCE_MODIFIERS = {"sealed", "static", "abstract"}
CSHARP_DESIGNED_FOR_INHERITANCE_PATTERN = re.compile(r"\b(?:virtual|abstract|protected)\b")


def blank_out_non_code(text):
    """コメントとリテラルを空白に置き換える。行番号がずれないように、改行は残す。"""
    return NON_CODE_PATTERN.sub(lambda match: re.sub(r"[^\n]", " ", match.group(0)), text)


def braced_body(code, open_brace):
    """open_brace の位置の { から、対応する } の手前までを返す。"""
    depth = 0
    for index in range(open_brace, len(code)):
        if code[index] == "{":
            depth += 1
        elif code[index] == "}":
            depth -= 1
            if depth == 0:
                return code[open_brace:index]
    return code[open_brace:]


def cpp_declares_virtual_destructor(body, name):
    name = re.escape(name)
    return bool(re.search(rf"\bvirtual\s+~\s*{name}\s*\(", body)
                or re.search(rf"~\s*{name}\s*\([^)]*\)[^;{{]*\boverride\b", body))


def cpp_violations(code):
    """final も virtual デストラクターもないクラスの (名前, 位置) を返す。"""
    for match in CPP_CLASS_HEAD_PATTERN.finditer(code):
        if CPP_ENUM_BEFORE_PATTERN.search(code, 0, match.start()):
            continue  # enum class は継承できない
        if match.group(2):
            continue  # final
        name = match.group(1)
        if not cpp_declares_virtual_destructor(braced_body(code, match.end() - 1), name):
            yield name, match.start(1)


def csharp_body(code, after_head):
    """型の本体を返す。本体のない宣言 (record X(int A);) なら空文字列。"""
    end = re.compile(r"[{;]").search(code, after_head)
    if end is None or code[end.start()] == ";":
        return ""
    return braced_body(code, end.start())


def csharp_violations(code):
    """sealed・static・abstract のいずれもなく、継承も想定していないクラスの (名前, 位置) を返す。"""
    for match in CSHARP_CLASS_HEAD_PATTERN.finditer(code):
        if CSHARP_INHERITANCE_MODIFIERS.intersection(match.group(1).split()):
            continue
        if CSHARP_DESIGNED_FOR_INHERITANCE_PATTERN.search(csharp_body(code, match.end())):
            continue
        yield match.group(2), match.start(2)


LANGUAGES = [
    # (拡張子, 違反を探す関数, 違反のメッセージ)
    ({".cpp", ".h", ".hpp", ".ixx"}, cpp_violations, "final も virtual デストラクターもない"),
    ({".cs"}, csharp_violations, "sealed・static・abstract のいずれもない"),
]


def source_files(extensions):
    for sources_root in sorted(ARTICLES_ROOT.glob("*/Sources")):
        for path in sorted(sources_root.rglob("*")):
            if (path.is_file() and path.suffix.lower() in extensions
                    and not EXCLUDED_DIRECTORY_NAMES.intersection(path.relative_to(sources_root).parts)):
                yield path


def main():
    checked = 0
    found = 0
    for extensions, find_violations, message in LANGUAGES:
        for path in source_files(extensions):
            checked += 1
            code = blank_out_non_code(path.read_text(encoding="utf-8-sig"))
            for name, offset in find_violations(code):
                found += 1
                line = code.count("\n", 0, offset) + 1
                print(f"{path.relative_to(REPOSITORY_ROOT).as_posix()}:{line}: {name} に {message}")
    print(f"確認したファイル: {checked}、違反: {found}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
