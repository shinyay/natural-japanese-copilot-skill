# リリース

[English](../en/releasing.md) | [README](../../README.md)

この文書はmaintainer向けです。公開version、repository、release asset、
ドキュメントの内容を一致させるための確認手順を示します。

## version

- skill version: `0.1.0`
- Git tag: `v0.1.0`
- repository: `shinyay/natural-japanese-copilot-skill`
- license: MIT
- copyright: Copyright (c) 2026 shinyay

versionを変更するときは、少なくとも次を同期します。

- `skills/natural-japanese-copilot/SKILL.md` のmetadata
- `README.md` と `README.en.md`
- `CHANGELOG.md`
- `docs/ja/installation.md` と `docs/en/installation.md`
- install commandとrelease notes
- asset file名

## release前の確認

### 1. 変更範囲

- skillの名前が `natural-japanese-copilot` で統一されている
- 明示指定が `/natural-japanese-copilot` で説明されている
- selectorを独立したslash commandとして説明していない
- runtime instructionsが日本語であることを日英docsで説明している
- `skills/natural-japanese-copilot/...` のpathが正しい

### 2. tests

```console
python -m unittest discover -s tests -v
```

このコマンドをPython 3.10、3.13、3.14で実行します。
v0.1.0の基準は、3つのversionで63件すべて成功です。件数が変わった場合は、
追加・削除の理由と新しい結果をCHANGELOGと評価文書へ反映します。

checkerの成功例、失敗例、複数surfaceも確認します。

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md --contract examples/contract.json --format json
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation-broken.md --contract examples/contract.json --format json
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/surfaces.json --contract examples/surfaces-contract.json --format json
```

期待する終了コードは順に`0`、`1`、`0`です。

### 3. semantic review

- 24件のcaseを確認する
- 変更した規則にpositive caseとnegative caseがある
- 8件の固定例で条件、否定、確度、数値、帰属を確認する
- 自動scoreや統計的評価として説明していない

### 4. 日英ドキュメント

- README、CONTRIBUTING、SECURITY、詳細docs、examples READMEが同期している
- コマンド、path、version、制限、観測結果が一致している
- 日本語から英語、英語から日本語の相互linkが有効
- UI画像がdevelopment buildの場合は、公開前の名称であることを画像と本文で明記する
- 公開名の表示を示す画像として使う場合は、公開名の実画面であることを確認する
- 未確認の効果や優位性を追加していない

### 5. セキュリティ

- checkerが標準ライブラリだけを使う
- checkerが外部通信やfile writeを行わない
- examples、logs、screenshotに秘密情報や個人情報がない
- vulnerability reportingの非公開経路を確認する

## release ZIP

GitHub repositoryとtagがinstallの基準です。release ZIPを添付する場合、
ZIPはこのプロジェクト固有の便宜的な成果物であり、Agent Skillsの
標準パッケージではありません。

推奨file名:

```text
natural-japanese-copilot-v0.1.0.zip
```

展開後は次の構成にします。

```text
natural-japanese-copilot/
├── SKILL.md
├── LICENSE
├── assets/
├── references/
└── scripts/
```

ZIPにはrepository全体、testsのtemporary file、cache、local settings、
認証情報を含めません。`scripts/build_release.py --verify-only`で
archive manifest、sourceとの差分、SHA-256を確認します。
checkerの実行は動作確認であり、package completenessの証明には使いません。

release notesには、ZIPが標準packageではないこと、推奨installが
`gh skill install`であることを明記します。

## Releaseとasset upload

mainのCIが成功した後、annotated tagをpushし、次でGitHub Releaseを
作成します。

```console
gh skill publish . --tag v0.1.0
```

Releaseが公開されると`.github/workflows/release.yml`が発火します。
workflowは公開tagをcheckoutし、validator、全tests、release build、
`--verify-only`を実行してから、ZIPと`SHA256SUMS`を同じReleaseへ
uploadします。Release workflowが成功し、両assetが表示されるまで
公開作業を完了扱いにしません。

## release notesに含める内容

- versionと主な変更
- 推奨install command
- GitHub CLI 2.90以降とPublic Previewであること
- Python 3.10以降が必要なのは任意checkerだけであること
- testsとmanual reviewの確認範囲
- 統計的評価ではないこと
- 既知の制限
- security reportingへのlink

推奨install command:

```powershell
gh skill install shinyay/natural-japanese-copilot-skill natural-japanese-copilot@v0.1.0 --agent github-copilot --scope user
```

## 公開後のsmoke check

1. 空のtest projectへtagを固定してproject installする。
2. `.agents/skills/natural-japanese-copilot/SKILL.md`を確認する。
3. 新しいCopilot App sessionを開始する。
4. 日本語promptと英語promptを1件ずつ試す。
5. 条件、否定、確度、数値、帰属が保持されるか確認する。
6. checkerの成功例と失敗例の終了コードを確認する。

publicなmainから個人用へ導入した公開名`natural-japanese-copilot`を、
新しいCopilot App sessionで読み込めることを確認済みです。
tag公開後は、同じ手順を`v0.1.0`へ固定して再確認します。
pickerがあるclientでは公開名の表示も確認し、結果にはclientとversionを
添えます。すべてのclientで同じUIになることはrelease条件にしません。

## 最終checklist

- [ ] version、tag、install commandが一致
- [ ] Python 3.10 / 3.13 / 3.14で63件のtestsがすべて成功
- [ ] positive / negative casesを確認
- [ ] 8件の固定例を確認
- [ ] 日英docsを同期
- [ ] link、path、掲載する画像の内容とalt textを確認
- [ ] 秘密情報を含まない
- [ ] optional ZIPの構成と説明を確認
- [ ] Release workflowが成功し、ZIPと`SHA256SUMS`が添付されている
- [ ] 公開名を使い、新しいApp sessionでloadを再確認
- [ ] CHANGELOGとrelease notesを更新
