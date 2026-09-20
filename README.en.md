# natural-japanese-copilot

[日本語](README.md)

`natural-japanese-copilot` is an Agent Skill for GitHub Copilot that helps
translate English into Japanese and draft or revise Japanese prose for its
reader and purpose without changing the meaning. It protects facts, numbers,
negation, conditions, certainty, attribution, and identifiers before
addressing translation-like or hard-to-read phrasing.

The runtime skill instructions are written in Japanese so they can express
fine-grained Japanese writing decisions. The public documentation is available
in both Japanese and English.

**Version:** v0.1.0<br>
**License:** MIT

## Quick start

`gh skill` is a Public Preview feature available in GitHub CLI 2.90 or later.

```powershell
gh skill install shinyay/natural-japanese-copilot-skill natural-japanese-copilot@v0.1.0 --agent github-copilot --scope user
```

This recommended command installs at personal scope. Use `--scope project`
for a project installation. The destinations are
`~/.copilot/skills/natural-japanese-copilot` and
`.agents/skills/natural-japanese-copilot`, respectively. Start a new Copilot
session after installation.

See [Installation](docs/en/installation.md) for the complete procedure.

## Usage

`/natural-japanese-copilot` is a skill selector, not an independent slash
command. Select it and include the task in the same request.

Japanese prompt example:

```text
/natural-japanese-copilot 次の英文を、条件、否定、確度、数値、帰属を保って自然な日本語に訳してください。
```

English prompt example:

```text
/natural-japanese-copilot Translate the following text into natural Japanese. Preserve conditions, negation, certainty, numbers, and attribution.
```

The skill can also help with Japanese drafting, revision, Markdown, documents,
slides, tables, and UI copy. It does not silently alter quotations, code,
commands, URLs, or machine-readable keys.

## Design goals and current evidence

### Design goals

- Reconstruct meaning in Japanese instead of copying English word order
- Protect facts, conditions, negation, certainty, numbers, and attribution
  before improving readability
- Make decisions for the reader, purpose, and artifact instead of applying
  one rewrite rule everywhere
- Review meaning and style as separate concerns

### Scope observed for v0.1.0

- All 63 unit tests passed on Python 3.10, 3.13, and 3.14
- 24 semantic review cases are included
- `natural-japanese-copilot`, installed from the public main branch, loaded
  successfully in a new Copilot App session
- Eight fixed examples preserved conditions, negation, certainty, numbers,
  and attribution

These are observations from limited environments and examples, not a
statistical evaluation. They do not establish a general improvement in
writing quality or guarantee behavior for every input or client. See
[Evaluation](docs/en/evaluation.md).

## Optional checker

`skills/natural-japanese-copilot/scripts/review_japanese.py` is an optional,
read-only checker that uses only the Python 3.10+ standard library.

- Inputs: UTF-8 `.md`, `.txt`, or surfaces JSON
- Optional contract JSON checks required literal strings and counts
- No external communication and no file modification
- Exit codes: `0`, `1`, and `2`

Exit code `0` does not guarantee correct meaning or natural Japanese. See
[Checker](docs/en/checker.md).

## Safety and limits

- The skill itself has no feature that sends document text to an external
  service.
- Copilot clients and models process data according to the configuration and
  policies of the environment in which they run. Check those rules before
  entering confidential material.
- The checker covers literal conditions and a small set of style hints. It
  cannot judge meaning, naturalness, or legal or technical correctness.
- The skill does not automatically publish, send, fact-check, or obtain expert
  review.
- A release ZIP is a project-specific convenience artifact, not a standard
  Agent Skills package.

Report security concerns according to the [Security Policy](SECURITY.en.md).

## Documentation

- [Installation](docs/en/installation.md)
- [Usage](docs/en/usage.md)
- [Design](docs/en/design.md)
- [Checker](docs/en/checker.md)
- [Evaluation](docs/en/evaluation.md)
- [Releasing](docs/en/releasing.md)
- [Examples](examples/README.en.md)

## Contributing / License

See [CONTRIBUTING.en.md](CONTRIBUTING.en.md) before proposing a change.
Japanese and English documentation must be updated together.

MIT License<br>
Copyright (c) 2026 shinyay
