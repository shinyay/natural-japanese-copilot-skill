from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


sys.dont_write_bytecode = True
REPOSITORY = Path(__file__).resolve().parents[1]
VALIDATOR = REPOSITORY.joinpath("scripts", "validate_repository.py")
BUILDER = REPOSITORY.joinpath("scripts", "build_release.py")
sys.path.insert(0, str(VALIDATOR.parent))

from validate_repository import (  # noqa: E402
    RELEASE_FILE_ALLOWLIST,
    validate_repository,
)


class RepositoryValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="repository-validator-")
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.create_valid_repository()

    def write(self, relative: str, content: str | bytes = "placeholder\n") -> Path:
        path = self.root.joinpath(*relative.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
        return path

    def create_valid_repository(self) -> None:
        mit_license = (
            "MIT License\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining "
            "a copy of this software.\n\n"
            'THE SOFTWARE IS PROVIDED "AS IS".\n'
        )
        root_files = {
            ".editorconfig": "root = true\n",
            ".gitattributes": "* text=auto eol=lf\n",
            ".gitignore": "dist/\n",
            "CHANGELOG.md": "# Changelog\n",
            "CONTRIBUTING.en.md": "# Contributing\n",
            "CONTRIBUTING.md": "# コントリビューション\n",
            "LICENSE": mit_license,
            "README.md": "# Natural Japanese\n",
            "README.en.md": "# Natural Japanese\n",
            "SECURITY.en.md": "# Security\n",
            "SECURITY.md": "# セキュリティ\n",
            ".github/ISSUE_TEMPLATE/bug_report.yml": "name: Bug\n",
            ".github/ISSUE_TEMPLATE/feature_request.yml": "name: Feature\n",
            ".github/pull_request_template.md": "# Pull request\n",
            ".github/workflows/ci.yml": "name: CI\n",
            ".github/workflows/release.yml": "name: Release\n",
            "examples/contract.json": "{}\n",
            "examples/copilot-instructions.md": "# Instructions\n",
            "examples/README.en.md": "# Examples\n",
            "examples/README.md": "# 例\n",
            "examples/source.txt": "Source\n",
            "examples/surfaces-contract.json": "{}\n",
            "examples/surfaces.json": "{}\n",
            "examples/translation-broken.md": "破損例\n",
            "examples/translation.md": "翻訳\n",
            "tests/test_build_release.py": "pass\n",
            "tests/test_evidence.py": "pass\n",
            "tests/test_repository_configuration.py": "pass\n",
            "tests/test_review_japanese.py": "pass\n",
            "tests/test_validate_repository.py": "pass\n",
            "docs/en/guide.md": "# Guide\n",
            "docs/evidence/app-development-check.json": "{}\n",
            "docs/evidence/app-v0.1.0-rc-check.json": "{}\n",
            "docs/ja/guide.md": "# ガイド\n",
        }
        for relative, content in root_files.items():
            self.write(relative, content)

        scripts = self.root.joinpath("scripts")
        scripts.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(VALIDATOR, scripts.joinpath("validate_repository.py"))
        shutil.copyfile(BUILDER, scripts.joinpath("build_release.py"))

        skill_prefix = "skills/natural-japanese-copilot/"
        for relative in RELEASE_FILE_ALLOWLIST:
            if relative.endswith(".json"):
                content = "{}\n"
            elif relative.endswith(".py"):
                content = (
                    'VERSION = "0.1.0"\n\n'
                    "def report():\n"
                    '    return {"tool_version": VERSION}\n'
                )
            elif relative == "LICENSE":
                content = mit_license
            else:
                content = "# Runtime resource\n"
            self.write(skill_prefix + relative, content)
        self.write(
            skill_prefix + "SKILL.md",
            "---\n"
            "name: natural-japanese-copilot\n"
            'description: "Write reliable, natural Japanese while preserving meaning."\n'
            "license: MIT\n"
            'compatibility: "Python 3.10+ for the optional checker."\n'
            "metadata:\n"
            '  version: "0.1.0"\n'
            "  author: example\n"
            "---\n\n"
            "# Natural Japanese\n\n"
            "See `references/translation.md`.\n",
        )

    def cli(self, root: Path | None = None) -> subprocess.CompletedProcess:
        target = root if root is not None else self.root
        result = subprocess.run(
            [sys.executable, "-B", str(VALIDATOR), "--root", str(target)],
            capture_output=True,
            encoding="utf-8",
            env={**dict(__import__("os").environ), "PYTHONUTF8": "1"},
            timeout=20,
            check=False,
        )
        self.assertIs(type(result.returncode), int)
        return result

    def test_valid_tree_and_scanner_source_pass(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("repository validation passed", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_frontmatter_name_directory_and_required_fields_are_checked(self):
        skill = self.root.joinpath(
            "skills", "natural-japanese-copilot", "SKILL.md"
        )
        original = skill.read_text(encoding="utf-8")
        skill.write_text(
            original.replace(
                "name: natural-japanese-copilot",
                "name: natural-japanese",
            ).replace(
                'compatibility: "Python 3.10+ for the optional checker."\n',
                "",
            ),
            encoding="utf-8",
            newline="\n",
        )
        errors = validate_repository(self.root)
        self.assertTrue(any("must match its directory" in error for error in errors))
        self.assertTrue(any("compatibility" in error for error in errors))

    def test_missing_resource_doc_pair_and_allowlists_are_reported(self):
        self.root.joinpath(
            "skills",
            "natural-japanese-copilot",
            "references",
            "translation.md",
        ).unlink()
        self.write("docs/en/only-english.md", "# Only English\n")
        self.write(
            "skills/natural-japanese-copilot/notes.md",
            "# Not a runtime file\n",
        )
        self.write("validation.log", "local validation output\n")
        errors = validate_repository(self.root)
        self.assertTrue(any("referenced resource is missing" in error for error in errors))
        self.assertTrue(any("documentation counterpart" in error for error in errors))
        self.assertTrue(any("release allowlist" in error for error in errors))
        self.assertTrue(any("public allowlist" in error for error in errors))

    def test_release_workflow_is_a_required_public_file(self):
        self.root.joinpath(".github", "workflows", "release.yml").unlink()
        errors = validate_repository(self.root)
        self.assertIn(
            "required public file is missing: .github/workflows/release.yml",
            errors,
        )

    def test_evidence_is_required_without_a_language_pair(self):
        for name in (
            "app-development-check.json",
            "app-v0.1.0-rc-check.json",
        ):
            with self.subTest(name=name):
                evidence = self.root.joinpath("docs", "evidence", name)
                evidence.unlink()
                errors = validate_repository(self.root)
                self.assertIn(
                    f"required public file is missing: docs/evidence/{name}",
                    errors,
                )
                evidence.write_text("{}\n", encoding="utf-8")

    def test_personal_paths_and_session_markers_are_rejected(self):
        content = "\n".join(
            (
                "C:" + "\\Users\\person\\private.txt",
                ".copilot/" + "session" + "-state",
            )
        )
        self.write("README.md", content + "\n")
        errors = validate_repository(self.root)
        self.assertTrue(any("personal absolute path" in error for error in errors))
        self.assertTrue(any("session or workstation metadata" in error for error in errors))
        result = self.cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("repository validation failed", result.stderr)

    def test_general_attribution_and_upstream_terms_are_allowed(self):
        self.write(
            "README.md",
            "# Terms\n\n"
            "Preserve attribution when translating claims.\n"
            "An ATTRIBUTION heading can describe semantic attribution.\n"
            "Use `--upstream` when the documented gh skill command requires it.\n"
            "The upstream branch is discussed without naming a research source.\n",
        )
        self.assertEqual(validate_repository(self.root), [])

    def test_named_source_files_are_rejected_at_the_public_root(self):
        self.write("ATTRIBUTION.md", "source notes\n")
        self.write("UPSTREAM-LICENSE.txt", "source license notes\n")
        errors = validate_repository(self.root)
        self.assertTrue(
            any("forbidden public-root source file: ATTRIBUTION.md" in error for error in errors)
        )
        self.assertTrue(
            any(
                "forbidden public-root source file: UPSTREAM-LICENSE.txt" in error
                for error in errors
            )
        )

    def test_runtime_and_frontmatter_versions_and_skill_license_are_checked(self):
        runtime = self.root.joinpath(
            "skills",
            "natural-japanese-copilot",
            "scripts",
            "review_japanese.py",
        )
        runtime.write_text(
            runtime.read_text(encoding="utf-8").replace("0.1.0", "0.2.0"),
            encoding="utf-8",
            newline="\n",
        )
        license_file = self.root.joinpath(
            "skills", "natural-japanese-copilot", "LICENSE"
        )
        license_file.write_text("not the expected license\n", encoding="utf-8")
        errors = validate_repository(self.root)
        self.assertTrue(any("VERSION must match" in error for error in errors))
        self.assertTrue(any("MIT license text is incomplete" in error for error in errors))

    def test_missing_root_is_an_input_error(self):
        missing = self.root.joinpath("does-not-exist")
        result = self.cli(missing)
        self.assertEqual(result.returncode, 2)
        self.assertIn("validation input error", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
