# Design

[日本語](../ja/design.md) | [README](../../README.en.md)

## Purpose

`natural-japanese-copilot` is an Agent Skill for reconstructing meaning in
Japanese for a particular reader and purpose rather than replacing words one
by one. Its priorities are:

1. The user's request and output requirements
2. The meaning of the original text or supplied material
3. Terminology, identifiers, and artifact constraints
4. Readability as Japanese

A rewrite that sounds natural but changes meaning is rejected.

## In scope and out of scope

In scope:

- English-to-Japanese translation
- Japanese drafting, proofreading, revision, and summarization
- Japanese in documents, slides, tables, HTML, and UI
- Meaning review for text with conditions and numbers

Out of scope:

- Assigning a numeric naturalness score
- Rewriting to evade AI classification or detection
- Inventing facts, experience, emotion, agreement, or deadlines
- Automatic fact-checking, publishing, sending, or expert review
- Replacing file-format-specific skills

## Structure

```text
skills/natural-japanese-copilot/
├── SKILL.md
├── LICENSE
├── assets/
│   ├── glossary-template.md
│   └── style-profile-template.md
├── references/
│   ├── artifact-profiles.md
│   ├── japanese-style.md
│   ├── review.md
│   ├── semantic-cases.json
│   └── translation.md
└── scripts/
    └── review_japanese.py
```

| Component | Role |
| --- | --- |
| `SKILL.md` | Priorities, boundaries, and the core process used for every task |
| `translation.md` | Translation, revision, and summarization with original text |
| `japanese-style.md` | Longer drafting, translation-like phrasing, and voice |
| `artifact-profiles.md` | Visible surfaces in documents, slides, tables, HTML, and UI |
| `review.md` | Separate checks for meaning and readability |
| `semantic-cases.json` | Positive and negative cases for human meaning review |
| `assets/*` | Optional glossary and style-profile templates |
| `review_japanese.py` | Optional read-only checker |

Only the references relevant to the current task need to be loaded.

## Units of meaning to preserve

The process reviews individual constraints, not just the overall impression.

| Constraint | Example failure |
| --- | --- |
| Condition | Turning “only if” into a guarantee that an action runs |
| Negation | Turning “not all” into total negation |
| Certainty | Turning “may” into a plan or decision |
| Numbers | Swapping an item count and a retry count |
| Attribution | Presenting a third party's claim as a verified fact |
| Modality | Confusing prohibition, lack of requirement, recommendation, and permission |
| Identifier | Translating an API name or command option |
| Structure | Moving a qualification from the visible surface into notes only |

Summaries may be shorter, but they retain conditions and uncertainty needed to
support the conclusion.

## Processing flow

### 1. Classify the task

Translation, proofreading, summarization, drafting, and diagnosis have
different allowed changes. A proofreading request is not permission to
replace the entire argument.

### 2. Identify the reader and artifact

Determine the reader, purpose, voice, visible surfaces, and verbatim
requirements. Ordinary ambiguity should not block the whole task, but
ambiguity that changes responsibility or deadlines should be surfaced.

### 3. Identify protected information

Record facts, subjects, numbers, units, conditions, negation, certainty,
attribution, terminology, and identifiers. Important artifacts may need
surface-specific relationships.

### 4. Reconstruct in Japanese

Write in units of meaning rather than copying English order. Preserve
structure and references when they are part of the requirements.

### 5. Review meaning and style separately

First check additions, omissions, stronger claims, and swapped relationships.
Then read the Japanese independently for particles, dependencies, excess
wording, and context.

### 6. Inspect the saved artifact

Headings, tables, figure labels, footnotes, notes, speaker notes, alternative
text, and UI messages are part of the result. Reviewing only a pre-render
draft is not sufficient.

## Why the runtime instructions are Japanese

The runtime instructions are maintained in Japanese so they can describe
Japanese particles, negation, certainty, and word combinations directly.
English-speaking users can still select the skill and write requests in
English. Public procedures, limits, and evaluation methods are available in
both languages.

## Style-rule policy

The skill does not ban a phrase in every context. Inanimate subjects, nominal
headings, or repeated polite endings can remain when they fit the artifact.
Checker findings are review candidates, not mandatory edits.

A new rule needs both:

- A positive case that the change improves
- A negative case where the same change must not be applied

This pairing limits overgeneralization from a local improvement.

## Data and external actions

The skill consists of static instructions and references and has no separate
feature that transmits document text. The checker only reads local files.
The surrounding Copilot environment still processes data according to its
product and organization settings. See the
[Security Policy](../../SECURITY.en.md).
