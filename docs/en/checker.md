# Checker

[日本語](../ja/checker.md) | [README](../../README.en.md)

## Overview

`skills/natural-japanese-copilot/scripts/review_japanese.py` is a command-line
checker that supports Japanese review.

- Python 3.10 or later
- Standard library only
- Reads local files only
- No external communication
- Does not modify input files or contracts

It is neither a translation engine nor a Japanese quality scorer. It reports
literal protection failures and a limited set of style-review candidates.

## Basic commands

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md
```

Use a contract and request JSON output:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md --contract examples/contract.json --format json
```

Usage:

```text
review_japanese.py INPUT [--contract FILE] [--profile PROFILE] [--format FORMAT]
```

| Option | Value |
| --- | --- |
| `INPUT` | UTF-8 `.md`, `.txt`, or `.json` using the surfaces schema |
| `--contract` | Literal contract JSON |
| `--profile` | `business`, `technical`, `slides`, or `ui`; default: `business` |
| `--format` | `text` or `json`; default: `text` |

UTF-8 BOM is supported. Empty input, NUL bytes, invalid UTF-8, an unsupported
extension, or a schema violation exits with `2`.

## `.md` and `.txt`

A `.txt` file is read as one `body` surface. A `.md` file is also one `body`
surface, but style review masks:

- Fenced code blocks
- Inline code
- URLs and link destinations
- HTML comments
- Block quotes

Headings, lists, tables, and link labels remain in style review. Masking only
affects style rules; literal contract checks inspect the original string.
Because this is not a complete Markdown parser, extract complex artifacts into
surfaces JSON.

## Surfaces JSON

Use surfaces to review separate visible or stored areas independently.

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

Each surface requires a unique `id`, a non-empty `kind`, `markup` set to
`plain` or `markdown`, and a string `text`. One surface may have empty text,
but all surfaces may not be empty. A `kind` of `code` or `quote` skips style
review only; contract checks still run.

See `examples/surfaces.json`.

## Contract JSON

A contract defines required literal strings and occurrence counts.

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

| Field | Meaning |
| --- | --- |
| `expected_surface_ids` | Every surface ID expected in the input |
| `id` | Unique check identifier |
| `surface` | Target surface ID; `"*"` counts across all surfaces |
| `source_excerpt` | A reference for a human returning to the original text |
| `allowed` | Accepted literal alternatives |
| `min_count` | Minimum occurrence count |
| `max_count` | Maximum count, or `null` only when no maximum applies |

Matching is literal, not regular-expression based. Case, full-width and
half-width characters, and Unicode forms are not normalized. When alternatives
overlap at the same position, the longer alternative is counted without
double-counting.

The checker does not establish that `source_excerpt` and `allowed` have the
same meaning. Build the contract from the original text before reviewing the
translation, and do not weaken it to fit a result. A bare literal such as
`"5"` also matches `"15"`; include enough surrounding text to bind the number
to its subject.

Missing or extra IDs relative to `expected_surface_ids` are errors. To catch a
number moved to another subject, target separate surfaces instead of relying
only on `surface: "*"`.

## Style-review candidates

The checker reports a small set of patterns as hints:

- Indirect capability phrasing
- Selected nominalized actions
- Context-free uncertainty endings
- Vague emphasis
- Empty introductions or conclusions
- Sentences over 120 characters in `business` and `technical`

The `slides` and `ui` profiles do not use the long-sentence hint. A hint is not
proof of an error, and no hints is not proof of natural writing.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | No contract error. Without a contract, the contract was not checked. Style hints may remain |
| `1` | Missing or excessive literals, missing or extra surfaces, or another contract mismatch |
| `2` | Input, contract, option, or invocation error; review did not complete |

Exit code `0` does not guarantee meaning, naturalness, factual accuracy, or
domain correctness. The JSON `semantic_review` field is always
`not_performed`.

## JSON result

Important fields:

| Field | Content |
| --- | --- |
| `contract_status` | `not_run`, `matched`, or `mismatch` |
| `style_status` | `reviewed` or `not_applicable` |
| `semantic_review` | Always `not_performed` |
| `surface_count` | Number of loaded surfaces |
| `style_hint_count` | Number of style hints |
| `contract_error_count` | Number of contract errors |
| `coverage` | Character counts, masked counts, Japanese counts, and excluded surfaces |
| `checks` | Literal counts and status for each check |
| `findings` | Error and hint locations, rules, and messages |

Input without Japanese has `style_status: "not_applicable"`. Without a
contract, `contract_status` is `not_run`.

## Examples

Passing contract:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md --contract examples/contract.json --format json
```

Intentional failure:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation-broken.md --contract examples/contract.json --format json
```

Multiple surfaces:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/surfaces.json --contract examples/surfaces-contract.json --format json
```

See [examples/README.en.md](../../examples/README.en.md).

## Limits

- Does not automatically detect semantic additions, omissions, or causality
- Cannot comprehensively find new information absent from the contract
- Does not directly parse advanced Markdown or Office files
- Cannot determine whether a flagged phrase is needed in context
- Produces no score or quality guarantee

Use the result as supporting information for comparison with the original text
and human review.
