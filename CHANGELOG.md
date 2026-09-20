# 変更履歴 / Changelog

このファイルには、公開バージョンの主な変更を記録します。

This file records notable changes in published versions.

## [0.1.0] - 2026-09-20

### 日本語

- `natural-japanese-copilot` skillの初回公開版
- 英日翻訳、日本語の新規執筆、推敲、成果物内の日本語に対応
- 意味を守るため、条件、否定、確度、数値、帰属、用語、識別子を
  分けて確認する手順を追加
- 文書、スライド、表、HTML、UIなどの表示面に応じた確認資料を追加
- Python 3.10以降の標準ライブラリだけで動く、読取専用checkerを追加
- literal contract、surfaces JSON、終了コード`0` / `1` / `2`に対応
- 日本語と英語の公開ドキュメント、examples、issue forms、
  pull request templateを追加
- Python 3.10、3.13、3.14で成功した63件のunit tests、
  24件のsemantic review cases、8件の固定例で
  v0.1.0の確認範囲を記録

### English

- Initial public release of the `natural-japanese-copilot` skill
- Supports English-to-Japanese translation, Japanese drafting and revision,
  and Japanese text in artifacts
- Adds a review process that treats conditions, negation, certainty, numbers,
  attribution, terminology, and identifiers as separate meaning constraints
- Adds guidance for visible surfaces in documents, slides, tables, HTML, and
  UI content
- Adds a read-only checker using only the Python 3.10+ standard library
- Supports literal contracts, surfaces JSON, and exit codes `0`, `1`, and `2`
- Adds Japanese and English public documentation, examples, issue forms, and
  a pull request template
- Records the v0.1.0 validation scope: 63 unit tests passing on Python 3.10,
  3.13, and 3.14, 24 semantic review cases, and eight fixed examples
