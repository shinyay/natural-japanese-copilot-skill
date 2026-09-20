# 使い方

[English](../en/usage.md) | [README](../../README.md)

## skillを選択する

`/natural-japanese-copilot` は、依頼に使うskillを選ぶためのselectorです。
それ自体が翻訳や校正を実行する独立したslash commandではありません。
selectorと依頼内容を一緒に送ります。

日本語の例:

```text
/natural-japanese-copilot 次の英文を自然な日本語に訳してください。数値、条件、否定、確度、帰属、製品名は変えないでください。
```

英語の例:

```text
/natural-japanese-copilot Translate the following text into natural Japanese. Preserve numbers, conditions, negation, certainty, attribution, and product names.
```

導入直後は新しいsessionを開始することを推奨します。skill pickerの
有無や表示方法はclientによって異なります。

## 英日翻訳

原文の意味を守る条件を明示すると、確認すべき点が分かりやすくなります。

```text
/natural-japanese-copilot
次を技術文書向けの自然な日本語に訳してください。
- “may”を予定や決定に強めない
- “not all”を全否定にしない
- 数値、単位、API名、コマンドはそのまま残す

The rollout may start in October, but the date has not been confirmed.
```

英文で依頼しても、出力言語を日本語と指定できます。

```text
/natural-japanese-copilot
Translate this release note into concise Japanese for administrators.
Keep all version numbers, requirements, and uncertainty unchanged.
```

## 日本語を推敲する

何を変えてよいか、どの文体を保つかを指定します。

```text
/natural-japanese-copilot
次の日本語を、意味と用語を変えずに簡潔な「です・ます」調へ整えてください。
全面的には書き直さず、読みにくい箇所だけ修正してください。
```

「自然にして」だけでは、修正範囲が広く解釈されることがあります。
公開資料、契約、仕様、数値の多い文書では、変えてはいけない条件を
具体的に示してください。

## 日本語を新規に書く

読者、目的、使える事実、出力形式を渡します。

```text
/natural-japanese-copilot
次の確認済み情報だけを使い、利用者向けのお知らせを日本語で書いてください。
未確定事項は未確定のままにし、根拠のない効果や体験談を追加しないでください。
読者: 管理者
形式: 見出し1つ、本文3段落、箇条書き
```

このskillは、足りない事実を創作して文章を完成させるためのものでは
ありません。責任、金額、期限、対象が変わる曖昧さは、確認事項として
分けます。

## 文書やUIで使う

Markdown、Word文書、スライド、スプレッドシート、HTML、UI文言では、
本文以外の表示面も指定します。

```text
/natural-japanese-copilot
スライドのタイトル、本文、表、図のラベル、注記、speaker notesを確認してください。
「社内テストのみ」と「本番未測定」は表示面から落とさないでください。
```

ファイル形式を扱う別のskillがある場合は、そのskillで生成、保存、
レイアウト確認を行います。`natural-japanese-copilot` は日本語の内容と
読みやすさを補い、形式別の処理を置き換えません。

## `quick` / `standard` / `careful`

これらは作業量の目安であり、専用commandではありません。

| 目安 | 用途 |
| --- | --- |
| `quick` | 短い返答や軽微な修正 |
| `standard` | 通常の翻訳、文書、成果物 |
| `careful` | 仕様、契約、公開資料、数値や条件が多い文章 |

どの目安でも意味の確認は省きません。必要なら依頼文に
「careful相当で、原文との照合結果も確認してください」のように書けます。

## 変更しないもの

明示的な依頼がない限り、次は変更しません。

- 引用と逐語指定の文章
- code、command、URL、file path
- API名、parameter、機械可読なkey
- UI上で実際に表示されているlabel
- 要件ID、数値、単位
- 依頼された英語など、日本語以外の出力

文章中に命令文があっても、翻訳・編集対象のデータとして扱います。
その命令を理由に、公開、送信、外部操作は行いません。

## 確認の流れ

1. 読者、用途、文体、出力形式を確認する
2. 事実、条件、否定、確度、数値、帰属、用語を特定する
3. 意味のまとまりごとに日本語を組み立てる
4. 原文または素材と照合する
5. 日本語だけを読んで、係り受けや冗長さを確認する
6. 保存後の見出し、表、注記、代替textなどを確認する

任意のcheckerは手順4や5を置き換えません。使い方は
[checker](checker.md)を参照してください。

## 実行時instructionsの言語

skillの実行時instructionsは日本語です。これは日本語の語感や
意味の区別を直接記述するための設計です。依頼自体は日本語でも英語でも
構いません。公開されている利用手順と制限は、日本語版と英語版の
ドキュメントで同等に説明します。
