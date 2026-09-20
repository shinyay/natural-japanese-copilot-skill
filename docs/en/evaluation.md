# Evaluation

[日本語](../ja/evaluation.md) | [README](../../README.en.md)

## What the evaluation separates

This project records design goals separately from observed results.

### Design goals

- Improve Japanese readability without changing meaning
- Preserve conditions, negation, certainty, numbers, attribution, and
  identifiers
- Keep important qualifications on the relevant artifact surface
- Avoid treating style hints as mechanical bans

These statements describe implementation intent. They do not by themselves
demonstrate an effect.

### Results observed for v0.1.0

| Area | Result | Supported interpretation |
| --- | --- | --- |
| Unit tests | All 63 passed on Python 3.10, 3.13, and 3.14 | Defined checker, release-layout, workflow, and evidence-record behavior |
| Semantic review cases | 24 cases | A case set for human comparison of meaning |
| Copilot App loading | The public name installed from public main succeeded in a new session | `natural-japanese-copilot` loaded in the observed App environment |
| Fixed examples | Eight preserved conditions, negation, certainty, numbers, and attribution | Those inputs and review dimensions |

## Unit tests

The unit tests cover:

- `.md`, `.txt`, and surfaces JSON input
- Included and masked areas in Markdown style review
- Profile-specific hints
- Literal contract counts, surfaces, and forbidden literals
- Strict JSON schemas and invalid input
- Read-only behavior
- CLI exit codes `0`, `1`, and `2`
- JSON results that do not claim a completed semantic review

Example:

```console
python -m unittest discover -s tests -v
```

This command was run with Python 3.10, 3.13, and 3.14.
GitHub Actions checks the same three versions.

The 63 passing tests support the defined checker, release-layout, workflow,
and evidence-record behavior.
They do not show that the skill produces natural Japanese for every text.

## Semantic review cases

`skills/natural-japanese-copilot/references/semantic-cases.json` contains 24
cases. Each case includes:

- Original text or task
- `acceptable`
- `unacceptable`
- Meaning `invariants`

The set covers capability, possibility, prohibition versus lack of
requirement, partial negation, necessary conditions, number-to-subject
relationships, percentages, time zones, unconfirmed schedules, attribution,
correlation versus causation, identifiers, requirements, UI labels, ambiguous
responsibility, absence of agreement, instructions inside quotations,
minimums, avoiding invented experience, and artifact surfaces.

A valid JSON structure is not evidence of high translation quality. These
cases support human meaning review, not automatic scoring.

## Eight fixed examples

For v0.1.0, eight repeatable inputs were reviewed for preservation of:

- Conditions
- Negation
- Certainty
- Number-to-subject relationships
- Attribution

This records that the selected dimensions were preserved in those eight
examples. It is not a random sample, controlled comparison, blind review, or
statistical test.
The public-name inputs, outputs, review dimensions, environment, and
uncaptured fields are published in
[`app-v0.1.0-rc-check.json`](../evidence/app-v0.1.0-rc-check.json).
The pre-rename record remains available in
[`app-development-check.json`](../evidence/app-development-check.json).

## App observation

`natural-japanese-copilot`, installed at personal scope from the public main
branch, loaded as a skill in a new Copilot App session. The release-candidate
record above includes the eight actual outputs and review method.

This result cannot be generalized to every Copilot client, version, operating
system, or organization configuration. UI presentation alone is not a
compatibility requirement.

### Picker display during development

![Development screenshot showing the pre-release natural-japanese name in the Copilot App Skill picker](../images/copilot-app-skill-picker-development.png)

The screenshot was captured before the public rename. It is included as an
observed example of an App Skill suggestion, not as evidence of the released
name or a guarantee that every client presents the same picker.

## Not evaluated

- Statistical improvement for a general user population
- Superiority over another skill or prompt
- Accuracy across every domain, voice, and document length
- Legal, medical, safety, or specialist technical validity
- AI-text classification or detection avoidance
- UI and loading behavior in every Copilot client

## Adding evidence

Record at least:

1. Version
2. Environment
3. Inputs or case set
4. Review dimensions
5. Pass/fail method
6. Limits on generalization

Pair every new rule with a positive and negative case. Do not publish an
average or percentage unless the sample, reviewers, criteria, and aggregation
method can also be described.
