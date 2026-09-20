# インストール

[English](../en/installation.md) | [README](../../README.md)

## 前提

- GitHub CLI 2.90以降
- Agent Skillsを利用できるGitHub Copilot環境
- インストール後に新しいsessionを開始できること

`gh skill` はPublic Previewです。CLIやクライアントの更新により、
表示や導入手順が変わる可能性があります。

バージョンを確認します。

```powershell
gh --version
gh skill --help
```

## 推奨: personal scopeへv0.1.0を導入する

複数のプロジェクトで使う場合は、次のコマンドを実行します。

```powershell
gh skill install shinyay/natural-japanese-copilot-skill natural-japanese-copilot@v0.1.0 --agent github-copilot --scope user
```

配置先:

```text
~/.copilot/skills/natural-japanese-copilot
```

この配置先は、GitHub CLI 2.98.0と隔離したHOMEで確認しています。
`@v0.1.0` を付けることで、既定branchの今後の変更ではなく、確認した
releaseを利用できます。

## project scope

プロジェクトごとにversionや挙動を固定する場合は、対象プロジェクトの
ディレクトリで実行します。

```powershell
gh skill install shinyay/natural-japanese-copilot-skill natural-japanese-copilot@v0.1.0 --agent github-copilot --scope project
```

配置先:

```text
.agents/skills/natural-japanese-copilot
```

このリポジトリ内の配布元は `skills/natural-japanese-copilot` です。
上記はGitHub CLI 2.98.0で `--agent github-copilot --scope project` を
実行して確認した配置先です。
personal scopeとproject scopeの両方に同名skillがある場合の優先順位は
クライアントに依存するため、意図しない重複を避けてください。

## 手動配置

`gh skill` を使わない場合は、リポジトリの
`skills/natural-japanese-copilot` ディレクトリを、そのまま次の
いずれかへコピーします。

- GitHub Copilotの手動project配置: `.github/skills/natural-japanese-copilot`
- Personal: `~/.copilot/skills/natural-japanese-copilot`

`SKILL.md` だけでなく、`assets`、`references`、`scripts`、`LICENSE`も
同じディレクトリ構成で配置してください。
手動project配置の`.github/skills/...`は、`gh skill install`の
project scopeが使う`.agents/skills/...`とは別です。

release ZIPが提供される場合、それはこのプロジェクト向けの便宜的な
成果物です。Agent Skillsの標準パッケージではありません。展開後の
ディレクトリ構成を確認してから上記の場所へ配置してください。

## 読み込みを確認する

1. 導入先に `SKILL.md` があることを確認する。
2. 導入前から開いていたsessionを閉じ、新しいCopilot sessionを開始する。
3. クライアントにskill pickerまたは利用可能なskill一覧がある場合は、
   `natural-japanese-copilot` を探す。
4. 短い依頼で選択を確認する。

```text
/natural-japanese-copilot 「The date has not been confirmed.」を、確度を変えずに自然な日本語へ訳してください。
```

pickerの有無や表示方法はクライアントによって異なります。pickerが
なくても、クライアントがskillを読み込める場合があります。

## 読み込まれない場合

- GitHub CLIが2.90以降か確認する
- ディレクトリ名が `natural-japanese-copilot` か確認する
- `SKILL.md` が導入先の直下にあるか確認する
- project scopeとpersonal scopeの重複を確認する
- 新しいsessionで試す
- 利用中のクライアントがAgent Skillsに対応しているか確認する

`/natural-japanese-copilot` はskill selectorであり、単独で実行する
slash commandではありません。選択後の依頼文も入力してください。

## versionを変更する

別versionへ切り替える場合は、skill名のtagを変更して再度導入します。
既存ファイルの置換が必要なときは、内容を確認したうえで
`gh skill install --help` に記載された上書きoptionを使ってください。
導入後は新しいsessionで確認します。
