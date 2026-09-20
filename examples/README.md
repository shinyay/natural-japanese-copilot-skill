# Examples

[English](README.en.md) | [README](../README.md)

このディレクトリには、skillの依頼例と、読取専用checkerの入力例が
あります。checkerはPython 3.10以降の標準ライブラリだけを使い、
外部通信や入力fileの変更を行いません。

## ファイル

| File | 内容 |
| --- | --- |
| `source.txt` | 条件、件数、回数、確度、識別子を含む英文 |
| `translation.md` | 保護条件を満たす日本語例 |
| `translation-broken.md` | 数値、確度、識別子を意図的に壊した例 |
| `contract.json` | 単一の`body` surface向けliteral contract |
| `surfaces.json` | slideのtitle、body、noteを分けた入力 |
| `surfaces-contract.json` | 各slide surfaceに対応するcontract |
| `copilot-instructions.md` | repository instructionsへ組み込める利用例 |

これらは挙動を確認する小さな例であり、benchmarkや統計的評価では
ありません。

## 成功するcontract

repository rootで実行します。

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md --contract examples/contract.json --format json
```

期待する結果:

- 終了コード`0`
- `contract_status`は`matched`
- `semantic_review`は`not_performed`

終了コード`0`は、contractに指定したliteral countへ違反していない
ことだけを示します。意味や自然さの保証ではありません。

PowerShellでは直後に終了コードを確認できます。

```powershell
$LASTEXITCODE
```

## 意図的に失敗するcontract

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation-broken.md --contract examples/contract.json --format json
```

期待する終了コードは`1`です。この例では、次を意図的に変更しています。

- 「最大5件、それぞれ1回」を「1件、最大5回」に入れ替える
- 「可能性がある、未確定」を「開始する、確定済み」に強める
- `--limit=5` と `fetch_items()` を別の文字列へ変える

checkerはcontractに書かれたliteralの不足・過剰を検出します。上の
意味変更を一般的に理解して判定しているわけではありません。

## 複数surface

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/surfaces.json --contract examples/surfaces-contract.json --profile slides --format json
```

期待する終了コードは`0`です。title、body、noteを別々に確認することで、
条件や未確定情報が別の面へ移動していないかを確認できます。

## Copilotで試す

導入後、新しいsessionでskillを選択し、`source.txt`の内容を渡します。

日本語prompt:

```text
/natural-japanese-copilot examples/source.txtを自然な日本語に訳してください。条件、否定、確度、数値と対象の対応、識別子を保持してください。
```

English prompt:

```text
/natural-japanese-copilot Translate examples/source.txt into natural Japanese. Preserve conditions, negation, certainty, number-to-subject relationships, and identifiers.
```

`/natural-japanese-copilot` はskill selectorであり、単独のslash command
ではありません。

## repository instructionsの例

`copilot-instructions.md` は、同じ方針をrepository instructionsへ
組み込む場合の短い例です。利用する前に内容を確認し、既存のinstructions
と競合しない範囲を選んでください。このfileを配置しただけでskillの
導入や選択が行われるわけではありません。

詳細は[checker](../docs/ja/checker.md)と
[評価](../docs/ja/evaluation.md)を参照してください。
