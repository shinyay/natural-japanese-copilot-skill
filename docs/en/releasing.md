# Releasing

[日本語](../ja/releasing.md) | [README](../../README.en.md)

This maintainer guide keeps the public version, repository, release artifacts,
and documentation aligned.

## Version

- Skill version: `0.1.0`
- Git tag: `v0.1.0`
- Repository: `shinyay/natural-japanese-copilot-skill`
- License: MIT
- Copyright: Copyright (c) 2026 shinyay

When changing the version, update at least:

- Metadata in `skills/natural-japanese-copilot/SKILL.md`
- `README.md` and `README.en.md`
- `CHANGELOG.md`
- `docs/ja/installation.md` and `docs/en/installation.md`
- Installation commands and release notes
- Asset file names

## Pre-release review

### 1. Scope and naming

- The skill name is consistently `natural-japanese-copilot`
- Explicit selection is documented as `/natural-japanese-copilot`
- The selector is not described as an independent slash command
- Both languages explain that runtime instructions are Japanese
- Paths use `skills/natural-japanese-copilot/...`

### 2. Tests

```console
python -m unittest discover -s tests -v
```

Run this command with Python 3.10, 3.13, and 3.14.
The v0.1.0 baseline is all 63 tests passing on all three versions. If the
count changes, record why and update the result in the changelog and
evaluation document.

Run the passing, failing, and multiple-surface checker examples:

```powershell
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation.md --contract examples/contract.json --format json
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/translation-broken.md --contract examples/contract.json --format json
python -B skills/natural-japanese-copilot/scripts/review_japanese.py examples/surfaces.json --contract examples/surfaces-contract.json --format json
```

Expected exit codes are `0`, `1`, and `0`.

### 3. Semantic review

- Review all 24 cases
- Pair each changed rule with a positive and negative case
- Review eight fixed examples for conditions, negation, certainty, numbers,
  and attribution
- Do not describe cases as automatic scoring or statistical evaluation

### 4. Japanese and English documentation

- Synchronize README, CONTRIBUTING, SECURITY, detailed docs, and examples
  README files
- Match commands, paths, versions, limits, and observed results
- Verify reciprocal links between Japanese and English
- If a UI image shows a development build, label the pre-release name in both
  the image and the surrounding text
- If an image is presented as the released selector, confirm that it shows the
  public name and has descriptive alternative text
- Remove unverified effect or superiority claims

### 5. Security

- Confirm that the checker uses only the standard library
- Confirm that it performs no external communication or file writes
- Remove secrets and personal data from examples, logs, and screenshots
- Confirm a private vulnerability-reporting route

## Release ZIP

The GitHub repository and tag are the installation reference. If a release ZIP
is attached, it is a project-specific convenience artifact, not a standard
Agent Skills package.

Recommended file name:

```text
natural-japanese-copilot-v0.1.0.zip
```

Extracted structure:

```text
natural-japanese-copilot/
├── SKILL.md
├── LICENSE
├── assets/
├── references/
└── scripts/
```

Do not include the entire repository, test temporary files, caches, local
settings, or credentials. Use `scripts/build_release.py --verify-only` to
check the archive manifest, source contents, and SHA-256. Running the checker
is a smoke test, not proof that the package is complete.

Release notes must say that the ZIP is not a standard package and that
`gh skill install` is the recommended path.

## Release and asset upload

After the main-branch CI succeeds, push the annotated tag and create the
GitHub Release with:

```console
gh skill publish . --tag v0.1.0
```

Publishing the Release triggers `.github/workflows/release.yml`. The workflow
checks out the published tag, runs the validator and full test suite, builds
and verifies the release, and uploads the ZIP and `SHA256SUMS` to that Release.
Do not treat publication as complete until the Release workflow succeeds and
both assets are visible.

## Release notes

Include:

- Version and notable changes
- Recommended installation command
- GitHub CLI 2.90+ and Public Preview status
- Python 3.10+ is required only for the optional checker
- Unit-test and manual-review scope
- The fact that the evaluation is not statistical
- Known limits
- A link to security reporting

Recommended command:

```powershell
gh skill install shinyay/natural-japanese-copilot-skill natural-japanese-copilot@v0.1.0 --agent github-copilot --scope user
```

## Post-release smoke check

1. Install the pinned tag at project scope in an empty test project.
2. Confirm `.agents/skills/natural-japanese-copilot/SKILL.md`.
3. Start a new Copilot App session.
4. Try one Japanese prompt and one English prompt.
5. Check preservation of conditions, negation, certainty, numbers, and
   attribution.
6. Check the passing and failing checker exit codes.

`natural-japanese-copilot`, installed at personal scope from public main, has
loaded successfully in a new Copilot App session. After publishing the tag,
repeat the check pinned to `v0.1.0`. Where a client has a picker, check the
public name there and record the client and version. The same UI is not a
release requirement across all clients.

## Final checklist

- [ ] Version, tag, and installation command match
- [ ] All 63 tests pass on Python 3.10, 3.13, and 3.14
- [ ] Positive and negative cases reviewed
- [ ] Eight fixed examples reviewed
- [ ] Japanese and English docs synchronized
- [ ] Links, paths, and any included image content and alternative text checked
- [ ] No secrets included
- [ ] Optional ZIP structure and wording checked
- [ ] Release workflow succeeded and attached the ZIP and `SHA256SUMS`
- [ ] Loading under the public name rechecked in a new App session
- [ ] Changelog and release notes updated
