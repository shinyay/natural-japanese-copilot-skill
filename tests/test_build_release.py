from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


sys.dont_write_bytecode = True
REPOSITORY = Path(__file__).resolve().parents[1]
BUILDER = REPOSITORY.joinpath("scripts", "build_release.py")
sys.path.insert(0, str(BUILDER.parent))

from build_release import (  # noqa: E402
    FIXED_ZIP_TIMESTAMP,
    REGULAR_FILE_MODE,
    RELEASE_FILE_ALLOWLIST,
    SKILL_NAME,
)


class ReleaseBuilderTests(unittest.TestCase):
    VERSION = "0.1.0"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="release-builder-")
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.skill = self.root.joinpath("skills", SKILL_NAME)
        for relative in RELEASE_FILE_ALLOWLIST:
            path = self.skill.joinpath(*relative.split("/"))
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative == "SKILL.md":
                content = (
                    "---\n"
                    "name: natural-japanese-copilot\n"
                    "description: Test fixture.\n"
                    "license: MIT\n"
                    "compatibility: Python 3.10+\n"
                    "metadata:\n"
                    f'  version: "{self.VERSION}"\n'
                    "---\n"
                )
            elif relative == "scripts/review_japanese.py":
                content = (
                    "from __future__ import annotations\n\n"
                    f'VERSION = "{self.VERSION}"\n'
                )
            elif relative.endswith(".json"):
                content = '{"version": 1}\n'
            elif relative == "LICENSE":
                content = "MIT License\n"
            else:
                content = f"# {relative}\n"
            path.write_text(content, encoding="utf-8", newline="\n")

        excluded = {
            "tests/test_runtime.py": "raise AssertionError\n",
            "docs/internal.md": "internal\n",
            "__pycache__/review.cpython-314.pyc": b"bytecode",
            ".secret": "hidden\n",
            "references/.draft.md": "hidden\n",
        }
        for relative, content in excluded.items():
            path = self.skill.joinpath(*relative.split("/"))
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8", newline="\n")

    @property
    def archive(self) -> Path:
        return self.root.joinpath(
            "dist", f"{SKILL_NAME}-v{self.VERSION}.zip"
        )

    @property
    def checksums(self) -> Path:
        return self.root.joinpath("dist", "SHA256SUMS")

    def cli(
        self, version: str | None = None, *extra: str
    ) -> subprocess.CompletedProcess:
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(BUILDER),
                "--root",
                str(self.root),
                "--version",
                version if version is not None else self.VERSION,
                *extra,
            ],
            capture_output=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"},
            timeout=30,
            check=False,
        )
        self.assertIs(type(result.returncode), int)
        return result

    def test_archive_manifest_metadata_content_and_hash(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.archive.is_file())
        self.assertTrue(self.checksums.is_file())
        self.assertEqual(
            {path.name for path in self.archive.parent.iterdir()},
            {self.archive.name, self.checksums.name},
        )

        expected_names = [
            f"{SKILL_NAME}/{relative}"
            for relative in sorted(RELEASE_FILE_ALLOWLIST)
        ]
        with zipfile.ZipFile(self.archive) as archive:
            infos = archive.infolist()
            self.assertEqual([info.filename for info in infos], expected_names)
            self.assertIn(f"{SKILL_NAME}/LICENSE", expected_names)
            self.assertTrue(
                archive.read(f"{SKILL_NAME}/LICENSE").startswith(b"MIT License")
            )
            self.assertIsNone(archive.testzip())
            for info in infos:
                with self.subTest(path=info.filename):
                    self.assertFalse(info.is_dir())
                    self.assertEqual(info.date_time, FIXED_ZIP_TIMESTAMP)
                    self.assertEqual(info.create_system, 3)
                    self.assertEqual(info.external_attr >> 16, REGULAR_FILE_MODE)
                    relative = info.filename.removeprefix(f"{SKILL_NAME}/")
                    self.assertEqual(
                        archive.read(info),
                        self.skill.joinpath(*relative.split("/")).read_bytes(),
                    )

        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.assertEqual(
            self.checksums.read_text(encoding="ascii"),
            f"{digest}  {self.archive.name}\n",
        )
        verified = self.cli(None, "--verify-only")
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertIn("release verification passed", verified.stdout)

    def test_rebuild_is_deterministic_when_source_timestamps_change(self):
        first = self.cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        first_bytes = self.archive.read_bytes()
        first_sums = self.checksums.read_bytes()
        for path in self.skill.rglob("*"):
            if path.is_file():
                os.utime(path, (1893456000, 1893456000))
        second = self.cli()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.archive.read_bytes(), first_bytes)
        self.assertEqual(self.checksums.read_bytes(), first_sums)

    def test_existing_outputs_are_replaced_without_deleting_unmanaged_files(self):
        dist = self.root.joinpath("dist")
        dist.mkdir()
        self.archive.write_bytes(b"old archive")
        self.checksums.write_text("old checksum\n", encoding="ascii")
        sentinel = dist.joinpath("keep.txt")
        sentinel.write_text("keep\n", encoding="utf-8")
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(self.archive.read_bytes(), b"old archive")
        self.assertTrue(self.checksums.read_text(encoding="ascii").endswith(
            f"  {self.archive.name}\n"
        ))
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep\n")

    def test_unsafe_versions_are_input_errors(self):
        for version in (
            "../0.1.0",
            "v0.1.0",
            "01.2.3",
            "1.2",
            "1.2.3-beta",
            "1.2.3/extra",
            " 1.2.3",
            "1" * 40 + ".2.3",
        ):
            with self.subTest(version=version):
                result = self.cli(version)
                self.assertEqual(result.returncode, 2)
                self.assertIn("release input error", result.stderr)
        self.assertFalse(self.root.joinpath("dist").exists())

    def test_requested_version_must_match_skill_and_runtime_versions(self):
        rejected_build = self.cli("9.9.9")
        self.assertEqual(rejected_build.returncode, 1)
        self.assertIn("version mismatch", rejected_build.stderr)
        self.assertFalse(
            self.root.joinpath(
                "dist", f"{SKILL_NAME}-v9.9.9.zip"
            ).exists()
        )

        built = self.cli()
        self.assertEqual(built.returncode, 0, built.stderr)
        rejected_verify = self.cli("9.9.9", "--verify-only")
        self.assertEqual(rejected_verify.returncode, 1)
        self.assertIn("version mismatch", rejected_verify.stderr)

    def test_runtime_version_mismatch_and_parse_failure_are_explicit(self):
        runtime = self.skill.joinpath("scripts", "review_japanese.py")
        runtime.write_text(
            runtime.read_text(encoding="utf-8").replace("0.1.0", "0.2.0"),
            encoding="utf-8",
            newline="\n",
        )
        mismatch = self.cli()
        self.assertEqual(mismatch.returncode, 1)
        self.assertIn("runtime VERSION='0.2.0'", mismatch.stderr)

        runtime.write_text("VERSION =\n", encoding="utf-8", newline="\n")
        invalid = self.cli()
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("cannot parse runtime checker VERSION", invalid.stderr)

    def test_unknown_runtime_file_and_tampered_archive_fail_closed(self):
        unknown = self.skill.joinpath("notes.md")
        unknown.write_text("not allowlisted\n", encoding="utf-8")
        rejected = self.cli()
        self.assertEqual(rejected.returncode, 1)
        self.assertIn("not allowlisted", rejected.stderr)
        self.assertFalse(self.archive.exists())

        unknown.unlink()
        built = self.cli()
        self.assertEqual(built.returncode, 0, built.stderr)
        with self.archive.open("ab") as stream:
            stream.write(b"tampered")
        verified = self.cli(None, "--verify-only")
        self.assertEqual(verified.returncode, 1)
        self.assertIn("release verification failed", verified.stderr)


if __name__ == "__main__":
    unittest.main()
