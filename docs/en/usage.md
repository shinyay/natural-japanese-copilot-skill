# Usage

[日本語](../ja/usage.md) | [README](../../README.en.md)

## Select the skill

`/natural-japanese-copilot` selects the skill for a request. It is not an
independent slash command that performs translation or editing by itself.
Send the selector and the task together.

Japanese example:

```text
/natural-japanese-copilot 次の英文を自然な日本語に訳してください。数値、条件、否定、確度、帰属、製品名は変えないでください。
```

English example:

```text
/natural-japanese-copilot Translate the following text into natural Japanese. Preserve numbers, conditions, negation, certainty, attribution, and product names.
```

Start a new session after installation. Skill-picker availability and
presentation vary by client.

## English-to-Japanese translation

State the constraints that must survive the translation.

```text
/natural-japanese-copilot
Translate the following into natural Japanese for technical documentation.
- Do not strengthen “may” into a plan or decision.
- Do not turn “not all” into total negation.
- Keep numbers, units, API names, and commands unchanged.

The rollout may start in October, but the date has not been confirmed.
```

A request written in English can explicitly require Japanese output:

```text
/natural-japanese-copilot
Translate this release note into concise Japanese for administrators.
Keep all version numbers, requirements, and uncertainty unchanged.
```

## Revise Japanese prose

Say what may change and which voice must remain.

```text
/natural-japanese-copilot
次の日本語を、意味と用語を変えずに簡潔な「です・ます」調へ整えてください。
全面的には書き直さず、読みにくい箇所だけ修正してください。
```

A broad request such as “make it natural” can leave the revision scope open.
For public material, contracts, specifications, or number-heavy text,
identify the conditions that must not change.

## Draft new Japanese text

Provide the reader, purpose, verified facts, and output format.

```text
/natural-japanese-copilot
Using only the verified facts below, write a Japanese notice for administrators.
Keep unresolved points unresolved, and do not add unsupported benefits or personal experience.
Format: one heading, three paragraphs, and a bullet list.
```

The skill is not intended to invent missing facts to complete a narrative.
Ambiguity that changes responsibility, cost, timing, or scope should be
reported as a question.

## Documents and UI surfaces

For Markdown, Word documents, slides, spreadsheets, HTML, or UI copy, include
surfaces outside the body.

```text
/natural-japanese-copilot
Review the slide title, body, table, figure labels, notes, and speaker notes.
Keep “internal test only” and “not measured in production” on the visible surface.
```

Use a format-specific skill, when available, for generation, saving, layout,
and rendering checks. `natural-japanese-copilot` complements those tools with
Japanese content guidance; it does not replace them.

## `quick`, `standard`, and `careful`

These names describe effort, not dedicated commands.

| Level | Typical use |
| --- | --- |
| `quick` | Short replies and small edits |
| `standard` | Ordinary translations, documents, and artifacts |
| `careful` | Specifications, contracts, public material, and text with many numbers or conditions |

Meaning review is required at every level. A request can say, for example,
“Use a careful review and compare the result with the original text.”

## Content that remains unchanged

Unless the user explicitly asks otherwise, the skill preserves:

- Quotations and verbatim text
- Code, commands, URLs, and file paths
- API names, parameters, and machine-readable keys
- Labels that must match the actual UI
- Requirement IDs, numbers, and units
- Requested output in English or another non-Japanese language

Instructions contained inside text being translated or edited are treated as
data. They are not a reason to publish, send, or perform an external action.

## Review flow

1. Identify the reader, purpose, voice, and output format.
2. Identify facts, conditions, negation, certainty, numbers, attribution, and
   terminology.
3. Reconstruct the meaning in Japanese.
4. Compare the draft with the original text or provided material.
5. Read the Japanese independently for grammar, relationships, and excess
   wording.
6. Check saved headings, tables, notes, alternative text, and other surfaces.

The optional checker does not replace steps 4 or 5. See
[Checker](checker.md).

## Language of the runtime instructions

The runtime instructions are written in Japanese so they can state Japanese
word choice, particles, negation, and certainty distinctions directly.
Requests may be written in Japanese or English. Public procedures and limits
are documented equivalently in both languages.
