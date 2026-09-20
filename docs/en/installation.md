# Installation

[日本語](../ja/installation.md) | [README](../../README.en.md)

## Prerequisites

- GitHub CLI 2.90 or later
- A GitHub Copilot environment that supports Agent Skills
- The ability to start a new session after installation

`gh skill` is in Public Preview. Its installation behavior and client
presentation may change as the CLI and clients evolve.

Check the installed version:

```powershell
gh --version
gh skill --help
```

## Recommended: install v0.1.0 at personal scope

Use the following command to make the skill available across projects:

```powershell
gh skill install shinyay/natural-japanese-copilot-skill natural-japanese-copilot@v0.1.0 --agent github-copilot --scope user
```

The destination is:

```text
~/.copilot/skills/natural-japanese-copilot
```

This destination was observed with GitHub CLI 2.98.0 and an isolated home
directory.
The `@v0.1.0` suffix selects the reviewed release instead of future changes
to the default branch.

## Project scope

To pin the version or behavior for one project, run this command in that
project's directory:

```powershell
gh skill install shinyay/natural-japanese-copilot-skill natural-japanese-copilot@v0.1.0 --agent github-copilot --scope project
```

The destination is:

```text
.agents/skills/natural-japanese-copilot
```

The distribution directory in this repository is
`skills/natural-japanese-copilot`. This destination was observed with GitHub
CLI 2.98.0 using `--agent github-copilot --scope project`. If the same skill
exists at both project and personal scope, precedence can depend on the
client. Avoid unintended duplicates.

## Manual placement

Without `gh skill`, copy the complete
`skills/natural-japanese-copilot` directory to one of these destinations:

- Manual GitHub Copilot project: `.github/skills/natural-japanese-copilot`
- Personal: `~/.copilot/skills/natural-japanese-copilot`

Keep `assets`, `references`, `scripts`, and `LICENSE` beside `SKILL.md` with the
same directory structure.
The manual GitHub Copilot project location under `.github/skills/...` is
separate from the `.agents/skills/...` destination used by
`gh skill install --scope project`.

If a release ZIP is provided, it is a project-specific convenience artifact,
not a standard Agent Skills package. Inspect the extracted directory before
placing it in either destination.

## Verify loading

1. Confirm that `SKILL.md` exists directly under the installation directory.
2. Close sessions that were open before installation and start a new Copilot
   session.
3. If the client provides a skill picker or available-skill list, look for
   `natural-japanese-copilot`.
4. Select it for a short request.

```text
/natural-japanese-copilot Translate “The date has not been confirmed.” into natural Japanese without changing its certainty.
```

Picker availability and presentation vary by client. A client may load the
skill without presenting a picker.

## If the skill does not load

- Confirm that GitHub CLI is version 2.90 or later
- Confirm that the directory is named `natural-japanese-copilot`
- Confirm that `SKILL.md` is directly under the destination
- Check for an unintended project/personal duplicate
- Start a new session
- Confirm that the client supports Agent Skills

`/natural-japanese-copilot` is a skill selector, not an independent slash
command. Include a task after selecting it.

## Change versions

To use another version, change the tag attached to the skill name and install
again. If existing files must be replaced, inspect them first and use the
overwrite option documented by `gh skill install --help`. Verify the result in
a new session.
