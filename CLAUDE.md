# CLAUDE.md

本リポジトリでは、プログラミングに関する Tips の記事を作成していく。

例:

- C# の最近の数バージョンの新機能の使用例
- C++ の最近の数バージョンの新機能の使用例
- JavaScript の最近の数バージョンの新機能の使用例

## フォーマット

- Markdown

## サンプルコード

- サンプルコードは、Markdown ファイルと同じフォルダーの下の `Sources/` フォルダーに置く。
- `Sources/` の下に、ソリューションごとにフォルダーを作成する。

```
Articles/CSharp/
├── <記事>.md
└── Sources/
    └── <ソリューション名>/
```

## 執筆ルール

文体・表記・書式の詳細は [執筆プロファイル.md](執筆プロファイル.md) に従う。

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
| `Reviews/` | レビュー結果を置く |

## 指示ファイルとスキルの同期

GitHub Copilot 向けのファイルは、Claude Code 向けのファイルから自動で同期する。同期先は直接編集しない。

| 正(編集する側) | 同期先 | 同期スクリプト |
|---|---|---|
| `CLAUDE.md` | `.github/copilot-instructions.md` | `.claude/hooks/sync_copilot_instructions.py` |
| `.claude/skills/` | `.github/skills/`(ミラーリング。正にないファイルは消す) | `.claude/hooks/sync_skills.py` |

- Claude Code の Edit / Write で正のファイルを編集すると、フック (`.claude/settings.json`) が同期スクリプトを実行する。
- それ以外の方法(Bash、エディター、Git の操作など)で正のファイルを変えたときは、同期スクリプトを `--force` 付きで手動実行する(例: `python3 .claude/hooks/sync_skills.py --force`)。
