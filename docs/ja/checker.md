# checker

[English](../en/checker.md) | [README](../../README.md)

## 概要

`skills/natural-japanese-copilot/scripts/review_japanese.py` は、日本語の
見直しを補助するcommand-line checkerです。

- Python 3.10以降
- 標準ライブラリのみ
- ローカルファイルを読取るだけ
- 外部通信なし
- 入力ファイルとcontractを変更しない

このcheckerは翻訳エンジンでも、日本語の採点器でもありません。
文字列の保護条件と、限定した文体の見直し候補を報告します。

## 基本実行

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md
```

contractを使い、JSONで結果を受け取る例:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md --contract examples/contract.json --format json
```

usage:

```text
review_japanese.py INPUT [--contract FILE] [--profile PROFILE] [--format FORMAT]
```

| option | 値 |
| --- | --- |
| `INPUT` | UTF-8の`.md`、`.txt`、またはsurfaces形式の`.json` |
| `--contract` | literal contract JSON |
| `--profile` | `business`、`technical`、`slides`、`ui`。既定は`business` |
| `--format` | `text`または`json`。既定は`text` |

UTF-8 BOMは読めます。空の入力、NULを含む入力、無効なUTF-8、未知の
拡張子、schema違反は終了コード`2`になります。

## `.md`と`.txt`

`.txt` は全体を `body` surfaceとして読みます。`.md` も単一の
`body` surfaceですが、文体検査では次を除外します。

- fenced code block
- inline code
- URLとlink destination
- HTML comment
- block quote

見出し、箇条書き、表、link labelは文体検査の対象です。除外は文体検査
だけに適用され、contractのliteral checkは元の文字列を確認します。
完全なMarkdown parserではないため、複雑な成果物はsurfaces JSONへ
抽出してください。

## surfaces JSON

複数の表示面を別々に確認するときに使います。

```json
{
  "version": 1,
  "surfaces": [
    {
      "id": "slide-03-title",
      "kind": "title",
      "markup": "plain",
      "text": "10月に展開開始の可能性"
    },
    {
      "id": "slide-03-note",
      "kind": "note",
      "markup": "plain",
      "text": "開始日はまだ確定していません。"
    }
  ]
}
```

各surfaceには、重複しない`id`、空でない`kind`、`plain`または
`markdown`の`markup`、文字列の`text`が必要です。`text`が空のsurfaceは
使えますが、全surfaceが空の入力は使えません。`kind`が`code`または
`quote`の場合は文体検査だけを除外し、contract checkは実行します。

実例は`examples/surfaces.json`を参照してください。

## contract JSON

contractは、守るべきliteralと出現回数を明示します。

```json
{
  "version": 1,
  "expected_surface_ids": ["body"],
  "checks": [
    {
      "id": "request-limit",
      "surface": "body",
      "source_excerpt": "at most five failed requests",
      "allowed": ["失敗したリクエストを最大5件"],
      "min_count": 1,
      "max_count": 1
    },
    {
      "id": "no-new-guarantee",
      "surface": "body",
      "source_excerpt": "The operation may fail.",
      "allowed": ["必ず成功"],
      "min_count": 0,
      "max_count": 0
    }
  ]
}
```

| field | 意味 |
| --- | --- |
| `expected_surface_ids` | 入力に存在する予定のsurface ID |
| `id` | checkを識別する一意のID |
| `surface` | 対象surface ID。`"*"`は全surfaceの合計 |
| `source_excerpt` | 人が原文へ戻るための手掛かり |
| `allowed` | 許容するliteralの候補 |
| `min_count` | 必要な最小出現回数 |
| `max_count` | 最大出現回数。上限なしの場合だけ`null` |

matchingは正規表現ではなくliteralです。大小文字、全角・半角、
Unicode表記を自動で正規化しません。候補が同じ位置で重なる場合は
長い候補を優先し、二重に数えません。

`source_excerpt` と `allowed` の意味が同じかはcheckerが判断しません。
原文を先に確認してcontractを作り、結果に合わせて条件を緩めないで
ください。裸の`"5"`では`"15"`にも一致するため、対象を含む十分に
長いliteralを使います。

`expected_surface_ids` に不足または追加があればerrorです。数値と対象の
入れ替わりを見つけたい場合は、`surface: "*"`ではなく、対応する
surfaceごとにcheckを置きます。

## 文体の見直し候補

checkerは、次のような限定したpatternをhintとして報告します。

- 間接的な能力表現
- 一部の名詞化した動作
- 文脈のない曖昧な語尾
- 根拠が不明な強調
- 内容のない導入・まとめ
- `business`と`technical`で120字を超える文

`slides`と`ui`では長文hintを使いません。hintがあることは誤りの証明
ではなく、hintがないことも自然さの証明ではありません。

## 終了コード

| code | 意味 |
| --- | --- |
| `0` | contract errorなし。contract未指定なら未検査。style hintは残り得る |
| `1` | literalの不足・過剰、surfaceの不足・追加などを検出 |
| `2` | 入力、contract、option、実行方法のerrorで検査未完了 |

終了コード`0`は、意味、自然さ、事実、専門分野の正確性を保証しません。
JSONの`semantic_review`は常に`not_performed`です。

## JSON結果

主なfield:

| field | 内容 |
| --- | --- |
| `contract_status` | `not_run`、`matched`、`mismatch` |
| `style_status` | `reviewed`または`not_applicable` |
| `semantic_review` | 常に`not_performed` |
| `surface_count` | 読み込んだsurface数 |
| `style_hint_count` | 文体hint数 |
| `contract_error_count` | contract error数 |
| `coverage` | 文字数、除外文字数、日本語文字数、除外surface |
| `checks` | checkごとのliteral countと状態 |
| `findings` | errorとhintの位置、規則、補足 |

日本語を含まない入力は`style_status: "not_applicable"`になります。
contractを指定していなければ`contract_status: "not_run"`です。

## examples

成功例:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md --contract examples/contract.json --format json
```

意図的な失敗例:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation-broken.md --contract examples/contract.json --format json
```

複数surface:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/surfaces.json --contract examples/surfaces-contract.json --format json
```

examplesの説明は[examples/README.md](../../examples/README.md)を参照して
ください。

## 制限

- 意味の追加、脱落、因果関係を自動判定しない
- literalに書かれていない新情報を網羅的に見つけない
- 高度なMarkdownやOffice fileを直接parseしない
- 文脈上必要な表現かどうかを判断しない
- scoreや品質保証を出さない

checkerの結果は、原文との照合と人による確認を補う情報として扱います。
