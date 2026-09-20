# コントリビューションガイド

[English](CONTRIBUTING.en.md)

バグ報告、改善案、ドキュメント修正、テスト追加を歓迎します。
変更は小さく保ち、何を改善し、何を変えないのかを明確にしてください。

## 始める前に

- セキュリティ上の問題は公開Issueに詳細を書かず、
  [SECURITY.md](SECURITY.md)に従って報告してください。
- 既存のIssueやpull requestに同じ提案がないか確認してください。
- 大きな仕様変更は、実装前にfeature requestで目的と制約を共有して
  ください。

## 開発環境

- Python 3.10以降
- checkerとtestsにはthird-party packageは不要
- GitHub CLIを使って導入動作を確認する場合は2.90以降
  （`gh skill`はPublic Preview）

unit tests:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

現在の全63件は、Python 3.10、3.13、3.14で成功しています。release前は
3つのversionすべてで確認してください。

```powershell
py -3.10 -m unittest discover -s tests -p "test_*.py"
py -3.13 -m unittest discover -s tests -p "test_*.py"
py -3.14 -m unittest discover -s tests -p "test_*.py"
```

checkerのexamples:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md --contract examples/contract.json --format json
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation-broken.md --contract examples/contract.json --format json
```

1つ目は終了コード`0`、2つ目は`1`になることを確認します。ただし、
`0`を意味や自然さの合格判定として扱わないでください。

## 変更の原則

- 自然さのために事実や意味を変えない
- 数値、単位、条件、否定、確度、帰属、用語、識別子を保持する
- 一つの不自然な例から、すべての文脈に適用する禁止ルールを作らない
- checkerの警告を減らすこと自体を目的にしない
- checkerは読取専用、外部通信なし、標準ライブラリのみという境界を保つ
- 新しい依存関係を追加する場合は、必要性と影響をpull requestに記載する

## positive / negative cases

skillの判断やcheckerの規則を変更する場合は、変更によって改善する
positive caseと、変えてはいけないnegative caseを追加してください。

- 意味に関する変更:
  `skills/natural-japanese-copilot/references/semantic-cases.json` に
  `acceptable` と `unacceptable` の両方を追加または更新する
- checkerの変更:
  `tests/test_review_japanese.py` に成功例と失敗例を追加する
- 特に、条件、否定、確度、数値と対象の対応、帰属、識別子の破損が
  見逃されないことを確認する

caseは自動的な翻訳スコアではありません。人が意味の差を確認できる、
短く具体的な例にしてください。

## 日本語と英語の同期

公開情報を変更するときは、日本語と英語を同じpull requestで更新します。

| 日本語 | English |
| --- | --- |
| `README.md` | `README.en.md` |
| `CONTRIBUTING.md` | `CONTRIBUTING.en.md` |
| `SECURITY.md` | `SECURITY.en.md` |
| `docs/ja/*.md` | `docs/en/*.md` |
| `examples/README.md` | `examples/README.en.md` |

単語単位で一致させる必要はありませんが、手順、制約、コマンド、
確認結果、注意事項は同等にしてください。片方だけの新機能説明や
古いversion表記を残さないでください。

## Pull request

pull requestには次を含めてください。

1. 変更の目的と範囲
2. 保持すべき意味や互換性
3. 実行したtestsと結果
4. 追加したpositive / negative cases
5. 日英ドキュメントを同期したか
6. セキュリティ、プライバシー、外部通信への影響

公開文書では、確認していない効果や一般的な優位性を主張しないで
ください。設計上の狙いと観測結果を分けて記載します。
