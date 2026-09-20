from __future__ import annotations

from pathlib import Path
import re
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
CI_WORKFLOW = REPOSITORY.joinpath(".github", "workflows", "ci.yml")
RELEASE_WORKFLOW = REPOSITORY.joinpath(".github", "workflows", "release.yml")
ACTION_PINS = {
    "actions/checkout": (
        "3d3c42e5aac5ba805825da76410c181273ba90b1",
        "v7.0.1",
    ),
    "actions/setup-python": (
        "5fda3b95a4ea91299a34e894583c3862153e4b97",
        "v7.0.0",
    ),
}


class RepositoryConfigurationTests(unittest.TestCase):
    def test_ci_matrix_permissions_and_commands(self):
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")
        self.assertRegex(workflow, r"(?m)^  push:$")
        self.assertRegex(workflow, r"(?m)^  pull_request:$")
        self.assertRegex(workflow, r"(?m)^permissions:\n  contents: read$")
        for version in ("3.10", "3.13", "3.14"):
            self.assertIn(f'"{version}"', workflow)
        for command in (
            "python -m unittest discover -s tests -v",
            "python scripts/validate_repository.py",
            "examples/translation.md",
            "python scripts/build_release.py --version 0.1.0",
            "--verify-only",
        ):
            self.assertIn(command, workflow)
        self.assertNotIn("pip install", workflow)
        self.assertNotIn("pytest", workflow)

    def test_official_actions_are_immutable_commit_pins(self):
        for workflow_path, expected_count in (
            (CI_WORKFLOW, 4),
            (RELEASE_WORKFLOW, 2),
        ):
            workflow = workflow_path.read_text(encoding="utf-8")
            uses = re.findall(
                r"(?m)^\s+uses:\s+"
                r"(actions/(?:checkout|setup-python))@([0-9a-f]{40})"
                r"\s+#\s+(v[0-9.]+)$",
                workflow,
            )
            self.assertEqual(len(uses), expected_count, workflow_path.name)
            for action, reference, comment in uses:
                with self.subTest(workflow=workflow_path.name, action=action):
                    self.assertEqual((reference, comment), ACTION_PINS[action])

    def test_release_workflow_checks_tagged_source_and_uploads_assets(self):
        workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertRegex(
            workflow,
            r"(?m)^  release:\n    types: \[published\]$",
        )
        self.assertRegex(workflow, r"(?m)^permissions:\n  contents: write$")
        self.assertIn("ref: ${{ github.event.release.tag_name }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('python-version: "3.14"', workflow)
        for command in (
            "python scripts/validate_repository.py",
            "python -m unittest discover -s tests -v",
            "python scripts/build_release.py",
            "--version ${{ steps.version.outputs.version }}",
            "--verify-only",
            'gh release upload "$RELEASE_TAG"',
            "dist/natural-japanese-copilot-v*.zip",
            "dist/SHA256SUMS",
            "--clobber",
        ):
            self.assertIn(command, workflow)
        self.assertIn("GH_TOKEN: ${{ github.token }}", workflow)
        self.assertNotIn("pip install", workflow)

    def test_editor_and_git_normalization_policies(self):
        editorconfig = REPOSITORY.joinpath(".editorconfig").read_text(
            encoding="utf-8"
        )
        self.assertIn("charset = utf-8", editorconfig)
        self.assertIn("end_of_line = lf", editorconfig)
        self.assertRegex(editorconfig, r"(?s)\[\*\.py\].*indent_size = 4")
        self.assertRegex(
            editorconfig,
            r"(?s)\[\*\.\{md,markdown\}\].*trim_trailing_whitespace = false",
        )

        attributes = REPOSITORY.joinpath(".gitattributes").read_text(
            encoding="utf-8"
        )
        self.assertIn("* text=auto eol=lf", attributes)
        self.assertIn("*.png binary", attributes)

        ignore = REPOSITORY.joinpath(".gitignore").read_text(encoding="utf-8")
        for pattern in ("__pycache__/", "dist/", ".coverage", ".idea/", ".vscode/"):
            self.assertIn(pattern, ignore)


if __name__ == "__main__":
    unittest.main()
