# Examples

[日本語](README.md) | [README](../README.en.md)

This directory contains sample skill requests and inputs for the read-only
checker. The checker uses only the Python 3.10+ standard library and performs
no external communication or input-file modification.

## Files

| File | Purpose |
| --- | --- |
| `source.txt` | English text with a condition, item and retry counts, certainty, and identifiers |
| `translation.md` | Japanese example that satisfies the protected literals |
| `translation-broken.md` | Intentionally damaged numbers, certainty, and identifiers |
| `contract.json` | Literal contract for one `body` surface |
| `surfaces.json` | Separate title, body, and note surfaces for a slide |
| `surfaces-contract.json` | Contract tied to each slide surface |
| `copilot-instructions.md` | Example text that can be incorporated into repository instructions |

These are small behavioral examples, not a benchmark or statistical
evaluation.

## Passing contract

Run from the repository root:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md --contract examples/contract.json --format json
```

Expected result:

- Exit code `0`
- `contract_status` is `matched`
- `semantic_review` is `not_performed`

Exit code `0` only means that the configured literal counts did not fail. It
does not guarantee meaning or natural Japanese.

In PowerShell, inspect the exit code immediately:

```powershell
$LASTEXITCODE
```

## Intentional contract failure

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation-broken.md --contract examples/contract.json --format json
```

The expected exit code is `1`. This example intentionally:

- Swaps “at most five items, once each” into “one item, at most five times”
- Strengthens “may, not confirmed” into “will, confirmed”
- Replaces `--limit=5` and `fetch_items()` with different strings

The checker detects missing or excessive literals defined by the contract. It
does not generally understand those semantic changes.

## Multiple surfaces

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/surfaces.json --contract examples/surfaces-contract.json --profile slides --format json
```

The expected exit code is `0`. Reviewing title, body, and note separately can
detect when a qualification or unresolved point has moved to another surface.

## Try it in Copilot

After installation, start a new session, select the skill, and provide
`source.txt`.

Japanese prompt:

```text
/natural-japanese-copilot examples/source.txtを自然な日本語に訳してください。条件、否定、確度、数値と対象の対応、識別子を保持してください。
```

English prompt:

```text
/natural-japanese-copilot Translate examples/source.txt into natural Japanese. Preserve conditions, negation, certainty, number-to-subject relationships, and identifiers.
```

`/natural-japanese-copilot` is a skill selector, not an independent slash
command.

## Repository-instructions example

`copilot-instructions.md` is a short example for incorporating the same policy
into repository instructions. Review it and select only the parts that do not
conflict with existing instructions. Placing that file alone does not install
or select the skill.

See [Checker](../docs/en/checker.md) and
[Evaluation](../docs/en/evaluation.md).
