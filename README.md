# natural-japanese-copilot

[English](README.en.md)

`natural-japanese-copilot` は、GitHub Copilotで英日翻訳、日本語の新規執筆、
推敲を行うときに、意味を保ちながら読み手と用途に合う日本語を組み立てる
ためのAgent Skillです。数値、否定、条件、確度、帰属、識別子などを
先に守り、そのうえで翻訳調や読みにくさを見直します。

実行時のskill instructionsは、細かな日本語の判断を扱うため日本語で
書かれています。公開ドキュメントは日本語と英語で提供します。

**Version:** v0.1.0<br>
**License:** MIT

## Quick start

`gh skill` はGitHub CLI 2.90以降で利用できるPublic Preview機能です。

```powershell
gh skill install shinyay/natural-japanese-copilot-skill natural-japanese-copilot@v0.1.0 --agent github-copilot --scope user
```

この推奨コマンドはpersonal scopeへ導入します。プロジェクト単位で
導入する場合は `--scope project` を指定します。導入先はそれぞれ
`~/.copilot/skills/natural-japanese-copilot` と
`.agents/skills/natural-japanese-copilot` です。導入後は、新しい
Copilot sessionを開始してください。

詳しい手順は[インストール](docs/ja/installation.md)を参照してください。

## 使い方

`/natural-japanese-copilot` はskill selectorです。単独で処理を実行する
slash commandではないため、選択後に依頼内容も入力します。

日本語での依頼例:

```text
/natural-japanese-copilot 次の英文を、条件、否定、確度、数値、帰属を保って自然な日本語に訳してください。
```

英語での依頼例:

```text
/natural-japanese-copilot Translate the following text into natural Japanese. Preserve conditions, negation, certainty, numbers, and attribution.
```

翻訳だけでなく、日本語の下書き、既存文の推敲、Markdown、文書、
スライド、表、UI文言などにも使えます。引用、コード、コマンド、
URL、機械可読なキーは勝手に変更しません。

## 設計上の狙いと現在の確認結果

### 設計上の狙い

- 英語の語順をなぞるのではなく、日本語として意味を組み立て直す
- 読みやすさより先に、事実、条件、否定、確度、数値、帰属を守る
- 一律の言い換えではなく、読者、用途、文書形式に合わせて判断する
- 意味の確認と文体の確認を分ける

### v0.1.0で確認済みの範囲

- Python 3.10、3.13、3.14で63件のunit testsがすべて成功
- 24件のsemantic review casesを用意
- 公開改名前に、同じruntime instructionsを使うdevelopment buildが
  新しいCopilot App sessionで読み込まれることを確認
- 8件の固定例で、条件、否定、確度、数値、帰属の保持を確認

これは限定した環境と例での観測結果であり、統計的評価ではありません。
文章品質の一般的な向上や、すべての入力・クライアントでの動作を保証
するものではありません。詳しくは[評価](docs/ja/evaluation.md)を参照して
ください。

## 補助checker

`skills/natural-japanese-copilot/scripts/review_japanese.py` は、
Python 3.10以降の標準ライブラリだけで動く、任意利用の読取専用
checkerです。

- 入力: UTF-8の `.md`、`.txt`、またはsurfaces JSON
- 任意のcontract JSONで、指定文字列の有無と回数を確認
- 外部通信とファイル変更を行わない
- 終了コード: `0`、`1`、`2`

終了コード`0`は、意味や自然さが正しいことを保証しません。
詳しくは[checker](docs/ja/checker.md)を参照してください。

## 安全性と制限

- このskill自体には、本文を外部へ送信する機能はありません。
- Copilotクライアントやモデルによるデータ処理は、利用環境の設定と
  ポリシーに従います。機密情報を入力する前に確認してください。
- checkerは文字列条件と一部の文体候補を確認する補助ツールであり、
  意味、自然さ、法務・技術上の正確性を判定しません。
- 公開、送信、事実確認、専門家レビューを自動で行いません。
- release ZIPは、このプロジェクト独自の便宜的な成果物であり、
  Agent Skillsの標準パッケージではありません。

セキュリティ上の問題は[Security Policy](SECURITY.md)に従って報告して
ください。

## ドキュメント

- [インストール](docs/ja/installation.md)
- [使い方](docs/ja/usage.md)
- [設計](docs/ja/design.md)
- [checker](docs/ja/checker.md)
- [評価](docs/ja/evaluation.md)
- [リリース](docs/ja/releasing.md)
- [examples](examples/README.md)

## Contributing / License

変更を提案する場合は[CONTRIBUTING.md](CONTRIBUTING.md)を参照して
ください。日本語と英語のドキュメントは同じ変更で同期します。

MIT License<br>
Copyright (c) 2026 shinyay
