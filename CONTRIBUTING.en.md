# Contributing

[日本語](CONTRIBUTING.md)

Bug reports, improvement proposals, documentation fixes, and tests are
welcome. Keep each change focused, and state what it improves and what must
remain unchanged.

## Before you start

- Do not put vulnerability details in a public issue. Follow
  [SECURITY.en.md](SECURITY.en.md).
- Check existing issues and pull requests for the same proposal.
- For a substantial behavior change, open a feature request first to describe
  the goal and constraints.

## Development environment

- Python 3.10 or later
- The checker and tests require no third-party packages
- GitHub CLI 2.90 or later when checking installation behavior
  (`gh skill` is in Public Preview)

Run the unit tests:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

All 63 current tests pass on Python 3.10, 3.13, and 3.14. Run the full suite
on all three versions before a release.

```powershell
py -3.10 -m unittest discover -s tests -p "test_*.py"
py -3.13 -m unittest discover -s tests -p "test_*.py"
py -3.14 -m unittest discover -s tests -p "test_*.py"
```

Run the checker examples:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md --contract examples/contract.json --format json
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation-broken.md --contract examples/contract.json --format json
```

The first command should exit with `0`; the second should exit with `1`.
Do not interpret `0` as proof of correct meaning or natural Japanese.

## Change principles

- Do not change facts or meaning to make a sentence sound more natural
- Preserve numbers, units, conditions, negation, certainty, attribution,
  terminology, and identifiers
- Do not turn one awkward example into a ban that applies in every context
- Do not optimize text merely to reduce checker hints
- Keep the checker read-only, offline, and limited to the standard library
- Explain the need and impact if a new dependency is proposed

## Positive and negative cases

When changing skill behavior or checker rules, add both a positive case that
should improve and a negative case that must not be changed.

- Meaning-related changes: add or update both `acceptable` and `unacceptable`
  in `skills/natural-japanese-copilot/references/semantic-cases.json`
- Checker changes: add passing and failing examples to
  `tests/test_review_japanese.py`
- Pay particular attention to conditions, negation, certainty, number-to-
  subject relationships, attribution, and identifiers

Cases are not an automatic translation score. Keep them short and concrete so
a reviewer can compare the meaning.

## Keep Japanese and English synchronized

Update both languages in the same pull request whenever public information
changes.

| Japanese | English |
| --- | --- |
| `README.md` | `README.en.md` |
| `CONTRIBUTING.md` | `CONTRIBUTING.en.md` |
| `SECURITY.md` | `SECURITY.en.md` |
| `docs/ja/*.md` | `docs/en/*.md` |
| `examples/README.md` | `examples/README.en.md` |

The wording need not be literal, but procedures, constraints, commands,
observations, and cautions must be equivalent. Do not leave a feature only in
one language or retain an obsolete version in one file.

## Pull requests

Include the following:

1. Purpose and scope
2. Meaning or compatibility that must be preserved
3. Tests run and their results
4. Positive and negative cases added
5. Whether Japanese and English documentation were synchronized
6. Security, privacy, and external-communication impact

Do not claim unverified effects or general superiority in public
documentation. Separate design goals from observed results.
