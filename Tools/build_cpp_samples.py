"""C++ のサンプルのプロジェクト (*.vcxproj) を g++ でビルドし、実行する。

- Articles/ の下の *.vcxproj ごとに、ClCompile のソースファイルを g++ でビルドする。
- 言語標準は、vcxproj の LanguageStandard (stdcpp14 など) を g++ の -std に読み替える。
  LanguageStandard がなければ、MSVC の既定の C++14 とする。
- ビルドしたプログラムを実行し、ビルドか実行に失敗したプロジェクトがあれば、
  終了コード 1 で終わる。MSVC でのビルドの代わりではなく、CI での簡易な確認に使う。
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ARTICLES_ROOT = REPOSITORY_ROOT / "Articles"

# vcxproj の LanguageStandard と、g++ の -std の値
GCC_STANDARDS = {
    "stdcpp14": "c++14",
    "stdcpp17": "c++17",
    "stdcpp20": "c++20",
    "stdcpp23": "c++23",
    "stdcpplatest": "c++2c",
}
DEFAULT_STANDARD = "c++14"

LANGUAGE_STANDARD_PATTERN = re.compile(r"<LanguageStandard>(\w+)</LanguageStandard>")
SOURCE_PATTERN = re.compile(r'<ClCompile Include="([^"]+)"')


def gcc_standard(project_text):
    match = LANGUAGE_STANDARD_PATTERN.search(project_text)
    return GCC_STANDARDS[match.group(1)] if match else DEFAULT_STANDARD


def build_and_run(project_path, output_directory):
    project_text = project_path.read_text(encoding="utf-8-sig")
    sources = [str(project_path.parent / source.replace("\\", "/"))
               for source in SOURCE_PATTERN.findall(project_text)]
    executable = output_directory / project_path.stem
    standard = gcc_standard(project_text)
    print(f"== {project_path.relative_to(REPOSITORY_ROOT).as_posix()} (-std={standard})", flush=True)
    if not sources:
        print("ソースファイルがない")
        return False
    build = subprocess.run(["g++", f"-std={standard}", "-Wall", "-Wextra", "-o", str(executable), *sources])
    return build.returncode == 0 and subprocess.run([str(executable)]).returncode == 0


def main():
    projects = sorted(ARTICLES_ROOT.rglob("*.vcxproj"))
    with tempfile.TemporaryDirectory() as output_directory:
        failed = [project for project in projects if not build_and_run(project, Path(output_directory))]
    for project in failed:
        print(f"失敗: {project.relative_to(REPOSITORY_ROOT).as_posix()}")
    print(f"プロジェクト: {len(projects)}、失敗: {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
