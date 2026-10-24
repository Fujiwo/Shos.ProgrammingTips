<!-- このファイルは CLAUDE.md から自動生成される。直接編集せず、CLAUDE.md を編集すること。 -->

# Copilot Instructions

本リポジトリでは、プログラミングに関する Tips の記事を作成していく。

例:

- C# の最近の数バージョンの新機能の使用例
- C++ の最近の数バージョンの新機能の使用例
- JavaScript の最近の数バージョンの新機能の使用例

## 新機能を紹介する記事に盛り込む内容

一つの記事では、原則として一つの機能を紹介する。記事の分量の目安は、本文 2,000〜3,000字とする(ただし必要に応じて増減してよい)。

プログラミング言語の最近の数バージョンの新機能を紹介する記事では、機能ごとに次を盛り込む。

- その機能を使うメリット
- その機能の意味
- その機能の使い方・書き方
- その機能のメリットを活かした、短く分かりやすいサンプル(分かりやすいコメント付き)

## 目次

- `Articles/README.md` に、プログラミング言語ごとの記事の目次を置く。記事のタイトルは、各記事の最初の H1 見出しから取る。
- 目次は `.claude/hooks/update_articles_toc.py` が自動生成する。直接編集しない。
- Claude Code の Edit / Write で `Articles/` の下の記事を追加・変更すると、フック (`.claude/settings.json`) が目次を更新する。
- 記事の削除・名前の変更や、Claude Code 以外での編集のあとは、`python3 .claude/hooks/update_articles_toc.py --force` を手動で実行する。
- 新しい言語のフォルダーを追加したときは、スクリプトの `LANGUAGES` に、フォルダー名と目次に表示する言語名を足す。

## フォーマット

- Markdown

## サンプルコード

- サンプルコードは、Markdown ファイルと同じフォルダーの下の `Sources/` フォルダーに置く。
- `Sources/` の下に、ソリューションごとにフォルダーを作成する。
- 記事ごとのサンプルコードは、動作チェックのため、`Sources/` の中にビルド・実行できる形で追加していく。
- 記事の中には、サンプルコードのうち説明に必要な部分だけを埋め込む。埋め込んだ部分は、`Sources/` のコードと一致させる。
- 言語ごとに一つのソリューション(JavaScript はフォルダー)を置き、記事ごとにプロジェクト(JavaScript はフォルダー)を追加する。サンプルに合った言語バージョンを指定する。
  - C#: `CSharpTips` ソリューションに新しいプロジェクトを追加し、`LangVersion` などでサンプルに合った言語バージョンを指定する。
  - C++: `CPlusplusTips` ソリューションに新しいプロジェクトを追加し、言語標準(`/std:c++20` など)でサンプルに合った言語バージョンを指定する。
  - JavaScript: `JavaScriptTips` フォルダーの下に記事ごとのフォルダーを作る。フォルダーには `package.json` を置き、`engines` でサンプルの動作に必要な Node.js のバージョンを指定する。

```
Articles/CSharp/
├── <記事>.md
└── Sources/
    └── CSharpTips/
        ├── CSharpTips.slnx
        └── <記事ごとのプロジェクト>/
```

- 各ソリューションの `Hello〜` プロジェクト(`HelloCSharpTips`、`HelloCPlusplusTips`)は、記事に対応しない雛形で、開発環境とソリューションがビルドできることの確認に使う。新しいプロジェクトを作るときの設定の基にもする。
- サンプルの確認には、次のスクリプトを使う。どちらも、GitHub Actions(`.github/workflows/check.yml`)が push と pull request のたびに実行する。
  - `python3 Tools/check_article_sources.py`: 記事に埋め込んだコードが `Sources/` のコードと一致するかを確認する。
  - `python3 Tools/build_cpp_samples.py`: C++ のプロジェクトを、`LanguageStandard` に合わせた g++ でビルド・実行する。MSVC でのビルドの代わりにはならない。

## 執筆ルール

文体・表記・書式の詳細は [執筆プロファイル.md](../執筆プロファイル.md) に従う。

## スキルの活用

`.claude/skills/` 内のスキルを、作業に応じて活用する。プロジェクト固有の約束事は `執筆プロファイル.md` が優先する。

- スキルは、どのリポジトリでも使える汎用的な内容に保つ。このリポジトリ固有の事情(フォルダー構成、書式ルール、検査のオプションなど)はスキルに書かず、この `CLAUDE.md` か `執筆プロファイル.md` に書く。
- スキルは、対象範囲や書式ルールを `CLAUDE.md` と `執筆プロファイル.md` から読んで動く。

| 作業 | 使うスキル |
|---|---|
| 記事の新規執筆・改稿・文体の診断 | `fujiwo-manuscript-voice`(中核4スキル `fujiwo-style`・`japanese-tech-writing`・`natural-japanese`・`stop-ai-slop-jp` を束ねる) |
| 記事の推敲(AIっぽさの除去、読みやすさの改善) | `yomiyasu`、`stop-ai-slop-jp`、`natural-japanese` |
| 記事全体のレビュー | `review-manuscript-natural-japanese` |
| Markdown の品質確認(リンク切れ、閉じていないコードフェンスなど) | `markdown-quality-audit` |
| サンプルコードの設計・実装・レビュー | `sustainable-code-jp` |

## フォルダーの使い方

| フォルダー | 用途 |
|---|---|
| `.github/prompts/` | 繰り返し使うプロンプトを置く |
| `Plans/` | 記事や作業の計画を置く |
| `Reviews/` | レビュー結果を置く。ファイル名は `<レビューの種類>-<対象>-<YYYYMMDD>.md` とする(例: `自然な日本語レビュー-CPlusplus11-lambda-20261024.md`)。対象は記事のファイル名から拡張子を除いたもので、リポジトリ全体が対象なら `-<対象>` を省く。同じ名前のファイルがあるときは、末尾に `-2`、`-3` と連番を付ける。スキルが別のファイル名を指定していても、この規則を優先する |
| `Tools/` | 記事とサンプルコードを検査するスクリプトを置く |

## 指示ファイルとスキルの同期

GitHub Copilot 向けのファイルは、Claude Code 向けのファイルから自動で同期する。同期先は直接編集しない。

| 正(編集する側) | 同期先 | 同期スクリプト |
|---|---|---|
| `CLAUDE.md` | `.github/copilot-instructions.md` | `.claude/hooks/sync_copilot_instructions.py` |
| `.claude/skills/` | `.github/skills/`(ミラーリング。正にないファイルは消す) | `.claude/hooks/sync_skills.py` |

- Claude Code の Edit / Write で正のファイルを編集すると、フック (`.claude/settings.json`) が同期スクリプトを実行する。
- それ以外の方法(Bash、エディター、Git の操作など)で正のファイルを変えたときは、同期スクリプトを `--force` 付きで手動実行する(例: `python3 .claude/hooks/sync_skills.py --force`)。
