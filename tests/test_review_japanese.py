from __future__ import annotations

import ast
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from copy import deepcopy
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import urllib.request
import webbrowser


sys.dont_write_bytecode = True
REPOSITORY = Path(__file__).resolve().parents[1]
SKILL = REPOSITORY.joinpath("skills", "natural-japanese-copilot")
SCRIPT = SKILL.joinpath("scripts", "review_japanese.py")
SEMANTIC_CASES = SKILL.joinpath("references", "semantic-cases.json")
sys.path.insert(0, str(SCRIPT.parent))

from review_japanese import (  # noqa: E402
    Surface,
    VERSION,
    load_surfaces,
    main as review_main,
    mask_markdown,
    parse_contract,
    parse_surfaces,
    read_json,
    review,
)


def one(text: str, markup: str = "plain", kind: str = "body") -> list[Surface]:
    return [Surface("body", kind, markup, text)]


def contract_data(
    allowed: list[str] | None = None, minimum: int = 1, maximum: int | None = 1
) -> dict:
    return {
        "version": 1,
        "expected_surface_ids": ["body"],
        "checks": [
            {
                "id": "limit",
                "surface": "body",
                "source_excerpt": "at most five requests",
                "allowed": allowed if allowed is not None else ["最大5件"],
                "min_count": minimum,
                "max_count": maximum,
            }
        ],
    }


def snapshot_directory(directory: Path) -> dict[str, tuple]:
    snapshot: dict[str, tuple] = {}
    for path in sorted(directory.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink():
            snapshot[relative] = ("symlink", os.readlink(path))
        elif path.is_dir():
            snapshot[relative] = ("directory",)
        elif path.is_file():
            content = path.read_bytes()
            stat = path.stat()
            snapshot[relative] = (
                "file",
                hashlib.sha256(content).hexdigest(),
                stat.st_size,
                stat.st_mtime_ns,
            )
        else:
            snapshot[relative] = ("other",)
    return snapshot


class StyleTests(unittest.TestCase):
    def test_flags_candidate_without_changing_text(self):
        original = "設定することができます。"
        surfaces = one(original)
        result = review(surfaces)
        self.assertEqual(result["style_hint_count"], 1)
        self.assertEqual(surfaces[0].text, original)
        self.assertEqual(result["contract_status"], "not_run")
        self.assertEqual(result["semantic_review"], "not_performed")

    def test_natural_technical_expressions_are_not_banned(self):
        text = "APIが値を返します。設定できます。すべての環境で動くわけではありません。"
        self.assertEqual(review(one(text))["style_hint_count"], 0)

    def test_headings_lists_tables_and_link_labels_are_checked(self):
        text = (
            "# 設定することができます\n"
            "- 設定することができます。\n"
            "| 項目 | 説明 |\n| --- | --- |\n"
            "| 機能 | 設定することができます。 |\n"
            "[設定することができます](https://example.invalid/guide)\n"
        )
        findings = review(one(text, "markdown"))["findings"]
        self.assertEqual(len(findings), 4)
        self.assertEqual([item["line"] for item in findings], [1, 2, 5, 6])

    def test_code_urls_comments_and_quotes_are_masked_for_style(self):
        text = (
            "~~~text\n設定することができます\n~~~\n"
            "``設定することができます ` 値``\n"
            "> 設定することができます。\n"
            "<!-- 設定することができます -->\n"
            "[参照](https://example.invalid/設定することができます)\n"
            "https://example.invalid/設定することができます\n"
        )
        result = review(one(text, "markdown"))
        self.assertEqual(result["style_hint_count"], 0)
        self.assertGreater(result["coverage"][0]["masked_characters"], 0)

    def test_masking_preserves_offsets_and_newlines(self):
        text = "説明\n```py\n確認を行います\n```\n設定することができます。\n"
        masked = mask_markdown(text)
        self.assertEqual(len(masked), len(text))
        self.assertEqual(
            [i for i, char in enumerate(masked) if char == "\n"],
            [i for i, char in enumerate(text) if char == "\n"],
        )
        finding = review(one(text, "markdown"))["findings"][0]
        self.assertEqual((finding["line"], finding["column"]), (5, 3))
        line = text.splitlines()[finding["line"] - 1]
        start = finding["column"] - 1
        self.assertEqual(line[start : start + len(finding["excerpt"])], finding["excerpt"])

    def test_fence_with_shorter_delimiter_does_not_end_code(self):
        text = "````\n```\n設定することができます\n````\n"
        self.assertEqual(review(one(text, "markdown"))["style_hint_count"], 0)

    def test_unclosed_fence_is_not_treated_as_prose(self):
        self.assertEqual(
            review(one("```text\n設定することができます", "markdown"))["style_hint_count"],
            0,
        )

    def test_plain_text_is_not_mistaken_for_markdown_code(self):
        self.assertEqual(review(one("`設定することができます`"))["style_hint_count"], 1)

    def test_masked_code_length_does_not_inflate_sentence_length(self):
        text = "識別子は`" + "x" * 200 + "`です。"
        self.assertEqual(review(one(text, "markdown"))["style_hint_count"], 0)

    def test_quotes_and_code_surfaces_skip_only_style(self):
        guard = parse_contract(contract_data(["設定することができます"]))
        for kind in ("quote", "code"):
            with self.subTest(kind=kind):
                result = review(one("設定することができます", kind=kind), guard)
                self.assertEqual(result["style_hint_count"], 0)
                self.assertEqual(result["contract_status"], "matched")
                self.assertTrue(result["coverage"][0]["style_excluded"])

    def test_long_sentence_threshold_and_profiles(self):
        for length in (120, 121):
            text = "あ" * (length - 1) + "。"
            for profile in ("business", "technical", "slides", "ui"):
                with self.subTest(length=length, profile=profile):
                    result = review(one(text), profile=profile)
                    expected = int(length == 121 and profile in ("business", "technical"))
                    self.assertEqual(result["style_hint_count"], expected)

    def test_non_japanese_is_explicitly_not_applicable(self):
        self.assertEqual(review(one("Hello world."))["style_status"], "not_applicable")

    def test_notes_and_labels_are_checked(self):
        surfaces = [
            Surface("note", "note", "plain", "設定することができます。"),
            Surface("label", "label", "plain", "設定することができます"),
        ]
        result = review(surfaces)
        self.assertEqual(result["style_hint_count"], 2)
        self.assertEqual({item["surface"] for item in result["findings"]}, {"note", "label"})


class ContractTests(unittest.TestCase):
    def test_good_and_changed_number_have_opposite_results(self):
        guard = parse_contract(contract_data())
        self.assertEqual(review(one("最大5件です。"), guard)["contract_status"], "matched")
        damaged = "最大15件です。"
        self.assertIn("15", damaged)
        self.assertNotIn("最大5件", damaged)
        result = review(one(damaged), guard)
        self.assertEqual(result["contract_status"], "mismatch")
        self.assertEqual(result["checks"][0]["found_count"], 0)

    def test_alternatives_overlap_without_double_counting(self):
        guard = parse_contract(contract_data(["最大5件", "最大5件まで"]))
        result = review(one("最大5件まで処理できます。"), guard)
        self.assertEqual(result["contract_status"], "matched")
        self.assertEqual(result["checks"][0]["matches"], {"最大5件まで": 1})

    def test_too_many_occurrences_are_reported(self):
        result = review(one("最大5件。最大5件。"), parse_contract(contract_data()))
        self.assertEqual(result["checks"][0]["found_count"], 2)
        self.assertEqual(result["contract_status"], "mismatch")

    def test_forbidden_literal_and_unlimited_count(self):
        forbidden = parse_contract(contract_data(["必ず成功"], 0, 0))
        self.assertEqual(review(one("失敗する場合があります。"), forbidden)["contract_status"], "matched")
        self.assertEqual(review(one("必ず成功します。"), forbidden)["contract_status"], "mismatch")
        unlimited = parse_contract(contract_data(["最大5件"], 1, None))
        self.assertEqual(review(one("最大5件。最大5件。"), unlimited)["contract_status"], "matched")

    def test_one_failed_check_fails_aggregate(self):
        data = contract_data()
        second = deepcopy(data["checks"][0])
        second.update(id="condition", allowed=["無効な場合に限り"])
        data["checks"].append(second)
        result = review(one("最大5件です。"), parse_contract(data))
        self.assertEqual([row["status"] for row in result["checks"]], ["matched", "mismatch"])
        self.assertEqual(result["contract_status"], "mismatch")
        self.assertEqual(result["contract_error_count"], 1)

    def test_swapped_values_fail_even_when_both_numbers_remain(self):
        data = contract_data(["上限5件"])
        data["expected_surface_ids"] = ["requests", "attempts"]
        data["checks"][0]["surface"] = "requests"
        second = deepcopy(data["checks"][0])
        second.update(id="attempts", surface="attempts", allowed=["上限1回"])
        data["checks"].append(second)
        guard = parse_contract(data)
        good = [
            Surface("requests", "table", "plain", "上限5件"),
            Surface("attempts", "table", "plain", "上限1回"),
        ]
        bad = [
            Surface("requests", "table", "plain", "上限1件"),
            Surface("attempts", "table", "plain", "上限5回"),
        ]
        self.assertEqual(review(good, guard)["contract_error_count"], 0)
        self.assertEqual(review(bad, guard)["contract_error_count"], 2)

    def test_condition_negation_and_uncertainty_have_good_and_damaged_cases(self):
        scenarios = (
            (
                "condition",
                "キャッシュが無効な場合、再試行します。",
                "再試行します。",
                "キャッシュが無効な場合",
            ),
            (
                "negation",
                "アクセストークンを保存してはいけません。",
                "アクセストークンを保存します。",
                "保存してはいけません",
            ),
            (
                "uncertainty",
                "展開は10月に始まる可能性があります。",
                "展開は10月に始まります。",
                "可能性があります",
            ),
        )
        for name, good, damaged, protected in scenarios:
            with self.subTest(name=name):
                guard = parse_contract(contract_data([protected]))
                self.assertEqual(review(one(good), guard)["contract_status"], "matched")
                result = review(one(damaged), guard)
                self.assertEqual(result["contract_status"], "mismatch")
                self.assertEqual(result["contract_error_count"], 1)

    def test_missing_or_extra_surface_is_not_silent(self):
        guard = parse_contract(contract_data())
        missing = review([Surface("title", "title", "plain", "最大5件")], guard)
        self.assertEqual(missing["contract_status"], "mismatch")
        self.assertEqual(
            {row["rule"] for row in missing["findings"]},
            {"missing-surface", "unexpected-surface"},
        )
        self.assertEqual(missing["checks"][0]["status"], "surface_missing")

    def test_exact_surface_set_accepts_match_and_rejects_each_direction(self):
        data = contract_data()
        data["expected_surface_ids"] = ["title", "body"]
        data["checks"][0]["surface"] = "body"
        guard = parse_contract(data)
        exact = [
            Surface("title", "title", "plain", "見出し"),
            Surface("body", "body", "plain", "最大5件です。"),
        ]
        self.assertEqual(review(exact, guard)["contract_status"], "matched")

        missing = review(exact[1:], guard)
        self.assertIn(
            ("missing-surface", "title"),
            {(item["rule"], item["surface"]) for item in missing["findings"]},
        )

        added = review(
            exact + [Surface("note", "note", "plain", "補足です。")],
            guard,
        )
        self.assertIn(
            ("unexpected-surface", "note"),
            {(item["rule"], item["surface"]) for item in added["findings"]},
        )

    def test_global_counts_do_not_join_unrelated_surfaces(self):
        data = contract_data(["最大5件"])
        data["expected_surface_ids"] = ["a", "b"]
        data["checks"][0]["surface"] = "*"
        surfaces = [
            Surface("a", "body", "plain", "最大"),
            Surface("b", "body", "plain", "5件"),
        ]
        self.assertEqual(review(surfaces, parse_contract(data))["contract_status"], "mismatch")

    def test_code_is_kept_for_contract_checks(self):
        guard = parse_contract(contract_data(["fetch_items()"]))
        text = "```python\nfetch_items()\n```\n結果を取得します。"
        self.assertEqual(review(one(text, "markdown"), guard)["contract_status"], "matched")

    def test_regex_characters_are_literal(self):
        guard = parse_contract(contract_data(["a.b()"]))
        self.assertEqual(review(one("aXb()"), guard)["contract_status"], "mismatch")
        self.assertEqual(review(one("a.b()"), guard)["contract_status"], "matched")

    def test_no_normalization_is_claimed(self):
        guard = parse_contract(contract_data(["最大5件"]))
        self.assertEqual(review(one("最大５件"), guard)["contract_status"], "mismatch")

    def test_bad_schema_and_count_types_are_rejected(self):
        mutations = [
            lambda d: d.update(extra=True),
            lambda d: d.update(version=True),
            lambda d: d.update(checks=[]),
            lambda d: d.update(expected_surface_ids=["body", "body"]),
            lambda d: d["checks"][0].update(min_count=True),
            lambda d: d["checks"][0].update(min_count=-1),
            lambda d: d["checks"][0].update(max_count=False),
            lambda d: d["checks"][0].update(max_count=0),
            lambda d: d["checks"][0].update(allowed=[]),
            lambda d: d["checks"][0].update(allowed=[""]),
            lambda d: d["checks"][0].update(allowed=["a", "a"]),
            lambda d: d["checks"][0].update(surface="typo"),
            lambda d: d["checks"][0].update(source_excerpt=""),
            lambda d: d["checks"][0].update(minimum_count=1),
            lambda d: d["checks"].append(deepcopy(d["checks"][0])),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                data = contract_data()
                mutate(data)
                with self.assertRaises(ValueError):
                    parse_contract(data)

    def test_report_post_image_has_meaningful_shape(self):
        result = review(one("最大15件です。"), parse_contract(contract_data()))
        self.assertEqual(
            {
                "version",
                "tool_version",
                "profile",
                "contract_status",
                "style_status",
                "semantic_review",
                "surface_count",
                "style_hint_count",
                "contract_error_count",
                "coverage",
                "checks",
                "findings",
            },
            set(result),
        )
        self.assertEqual(VERSION, "0.1.0")
        self.assertEqual(result["tool_version"], VERSION)
        self.assertEqual(result["surface_count"], len(result["coverage"]))
        self.assertEqual(result["contract_error_count"], 1)
        self.assertEqual(result["contract_status"], "mismatch")
        self.assertEqual(
            {
                "surface",
                "kind",
                "characters",
                "masked_characters",
                "japanese_characters",
                "style_excluded",
            },
            set(result["coverage"][0]),
        )
        self.assertEqual(result["coverage"][0]["surface"], "body")
        self.assertEqual(result["coverage"][0]["characters"], len("最大15件です。"))
        self.assertEqual(result["checks"][0]["id"], "limit")
        self.assertEqual(result["checks"][0]["status"], "mismatch")
        self.assertEqual(result["checks"][0]["found_count"], 0)
        self.assertEqual(result["findings"][0]["rule"], "protected-string-count")
        self.assertEqual(result["findings"][0]["check"], "limit")


class RuntimeSafetyTests(unittest.TestCase):
    def test_runtime_ast_uses_only_reviewed_imports_and_safe_calls(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"), filename=str(SCRIPT))
        allowed_modules = {
            "__future__",
            "argparse",
            "collections",
            "dataclasses",
            "json",
            "pathlib",
            "re",
            "sys",
            "typing",
        }
        forbidden_names = {
            "__import__",
            "compile",
            "delattr",
            "eval",
            "exec",
            "getattr",
            "globals",
            "locals",
            "open",
            "setattr",
            "vars",
        }
        forbidden_attributes = {
            "chmod",
            "connect",
            "execv",
            "execve",
            "flush",
            "hardlink_to",
            "lchmod",
            "mkdir",
            "open",
            "popen",
            "remove",
            "removedirs",
            "rename",
            "replace",
            "request",
            "rmdir",
            "spawnl",
            "spawnle",
            "spawnlp",
            "spawnlpe",
            "spawnv",
            "spawnve",
            "spawnvp",
            "spawnvpe",
            "symlink_to",
            "system",
            "touch",
            "truncate",
            "unlink",
            "urlopen",
            "write",
            "write_bytes",
            "write_text",
            "writelines",
        }
        violations: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] not in allowed_modules:
                        violations.append(
                            f"unapproved import {alias.name} at line {node.lineno}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level or module.split(".", 1)[0] not in allowed_modules:
                    violations.append(
                        f"unapproved import from {module!r} at line {node.lineno}"
                    )
                if any(alias.name == "*" for alias in node.names):
                    violations.append(f"star import at line {node.lineno}")
            elif isinstance(node, ast.Call):
                function = node.func
                if (
                    isinstance(function, ast.Attribute)
                    and function.attr in forbidden_attributes
                ):
                    violations.append(f"call .{function.attr} at line {node.lineno}")
                elif isinstance(function, ast.Name) and function.id in forbidden_names:
                    violations.append(f"call {function.id} at line {node.lineno}")
            elif (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "sys"
                and node.attr in {"meta_path", "modules", "path", "path_hooks"}
            ):
                violations.append(f"dynamic sys.{node.attr} access at line {node.lineno}")
            elif isinstance(node, ast.Name) and node.id == "__builtins__":
                violations.append(f"dynamic builtins access at line {node.lineno}")
        self.assertEqual(violations, [])

    def test_runtime_behavior_is_isolated_and_leaves_directory_unchanged(self):
        def blocked(*_args, **_kwargs):
            raise AssertionError("runtime attempted a forbidden side effect")

        with tempfile.TemporaryDirectory(prefix="review-safety-") as directory:
            root = Path(directory)
            path = root.joinpath("input.txt")
            path.write_text("自然な日本語です。", encoding="utf-8")
            contract = root.joinpath("contract.json")
            contract.write_text(
                json.dumps(contract_data(["自然な日本語"]), ensure_ascii=False),
                encoding="utf-8",
            )
            sentinel = root.joinpath("sibling", "sentinel.bin")
            sentinel.parent.mkdir()
            sentinel.write_bytes(b"\x00sentinel\xff")
            for candidate in (path, contract, sentinel):
                os.utime(candidate, (946684800, 946684800))
            before = snapshot_directory(root)
            stdout = io.StringIO()
            stderr = io.StringIO()
            patchers = [
                mock.patch.object(socket, "socket", side_effect=blocked),
                mock.patch.object(socket, "create_connection", side_effect=blocked),
                mock.patch.object(http.client.HTTPConnection, "connect", side_effect=blocked),
                mock.patch.object(http.client.HTTPConnection, "request", side_effect=blocked),
                mock.patch.object(webbrowser, "open", side_effect=blocked),
                mock.patch.object(subprocess, "Popen", side_effect=blocked),
                mock.patch.object(subprocess, "run", side_effect=blocked),
                mock.patch.object(subprocess, "call", side_effect=blocked),
                mock.patch.object(subprocess, "check_call", side_effect=blocked),
                mock.patch.object(subprocess, "check_output", side_effect=blocked),
                mock.patch.object(os, "system", side_effect=blocked),
                mock.patch.object(os, "popen", side_effect=blocked),
                mock.patch.object(os, "remove", side_effect=blocked),
                mock.patch.object(os, "removedirs", side_effect=blocked),
                mock.patch.object(os, "rename", side_effect=blocked),
                mock.patch.object(os, "replace", side_effect=blocked),
                mock.patch.object(os, "rmdir", side_effect=blocked),
                mock.patch.object(os, "unlink", side_effect=blocked),
                mock.patch.object(urllib.request, "urlopen", side_effect=blocked),
                mock.patch.object(Path, "chmod", side_effect=blocked),
                mock.patch.object(Path, "mkdir", side_effect=blocked),
                mock.patch.object(Path, "rename", side_effect=blocked),
                mock.patch.object(Path, "replace", side_effect=blocked),
                mock.patch.object(Path, "rmdir", side_effect=blocked),
                mock.patch.object(Path, "symlink_to", side_effect=blocked),
                mock.patch.object(Path, "touch", side_effect=blocked),
                mock.patch.object(Path, "unlink", side_effect=blocked),
                mock.patch.object(Path, "write_bytes", side_effect=blocked),
                mock.patch.object(Path, "write_text", side_effect=blocked),
            ]
            if hasattr(os, "startfile"):
                patchers.append(mock.patch.object(os, "startfile", side_effect=blocked))
            with ExitStack() as stack:
                for patcher in patchers:
                    stack.enter_context(patcher)
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    return_code = review_main(
                        [
                            str(path),
                            "--contract",
                            str(contract),
                            "--format",
                            "json",
                        ]
                    )
            after = snapshot_directory(root)
            self.assertEqual(return_code, 0)
            self.assertEqual(stderr.getvalue(), "")
            report = json.loads(stdout.getvalue())
            self.assertEqual(report["surface_count"], 1)
            self.assertEqual(report["contract_status"], "matched")
            self.assertEqual(after, before)


class InputAndCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="review-")
        self.directory = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def write(self, name: str, text: str) -> Path:
        path = self.directory.joinpath(name)
        path.write_text(text, encoding="utf-8")
        return path

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        environment = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *args],
            encoding="utf-8",
            capture_output=True,
            timeout=20,
            env=environment,
            check=False,
        )
        self.assertIs(type(result.returncode), int)
        return result

    def test_zero_for_hints_without_contract_is_not_semantic_success(self):
        path = self.write("draft.md", "設定することができます。")
        result = self.cli(str(path), "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["style_hint_count"], 1)
        self.assertEqual(report["tool_version"], VERSION)
        self.assertEqual(report["contract_status"], "not_run")
        self.assertEqual(report["semantic_review"], "not_performed")

    def test_cli_version_uses_runtime_version_and_starts_a_process(self):
        result = self.cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f"{SCRIPT.name} {VERSION}")
        self.assertEqual(result.stderr, "")

    def test_cli_good_bad_and_invalid_use_distinct_exit_codes(self):
        path = self.write("draft.txt", "最大5件です。")
        config = self.write("contract.json", json.dumps(contract_data(), ensure_ascii=False))
        good = self.cli(str(path), "--contract", str(config), "--format", "json")
        self.assertEqual(good.returncode, 0, good.stderr)
        path.write_text("最大15件です。", encoding="utf-8")
        bad = self.cli(str(path), "--contract", str(config), "--format", "json")
        self.assertEqual(bad.returncode, 1, bad.stderr)
        self.assertEqual(json.loads(bad.stdout)["contract_status"], "mismatch")
        config.write_text("not json", encoding="utf-8")
        invalid = self.cli(str(path), "--contract", str(config))
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("入力エラー", invalid.stderr)
        self.assertEqual(invalid.stdout, "")

    def test_unreadable_empty_binary_and_wrong_extension_fail(self):
        empty = self.write("empty.md", " \n")
        binary = self.write("binary.txt", "日本語\x00")
        wrong = self.write("wrong.pptx", "日本語")
        invalid_utf8 = self.directory.joinpath("encoding.txt")
        invalid_utf8.write_bytes(b"\xff\xfe\x80")
        missing = self.directory.joinpath("missing.txt")
        for path in (empty, binary, wrong, invalid_utf8, missing):
            with self.subTest(name=path.name):
                result = self.cli(str(path))
                self.assertEqual(result.returncode, 2)
                self.assertIn("入力エラー", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_invalid_options_fail(self):
        path = self.write("draft.txt", "本文です。")
        for args in (("--profile", "unknown"), ("--format", "html")):
            with self.subTest(args=args):
                self.assertEqual(self.cli(str(path), *args).returncode, 2)

    def test_read_only_hash_is_unchanged(self):
        path = self.write("draft.md", "設定することができます。\n")
        config = self.write(
            "contract.json",
            json.dumps(contract_data(["設定することができます"]), ensure_ascii=False),
        )
        fixed_time = 946684800
        os.utime(path, (fixed_time, fixed_time))
        os.utime(config, (fixed_time, fixed_time))
        before = {
            candidate: (
                hashlib.sha256(candidate.read_bytes()).hexdigest(),
                candidate.stat().st_mtime_ns,
            )
            for candidate in (path, config)
        }
        result = self.cli(str(path), "--contract", str(config))
        self.assertEqual(result.returncode, 0, result.stderr)
        after = {
            candidate: (
                hashlib.sha256(candidate.read_bytes()).hexdigest(),
                candidate.stat().st_mtime_ns,
            )
            for candidate in (path, config)
        }
        self.assertEqual(after, before)

    def test_utf8_bom_is_supported(self):
        path = self.write("bom.txt", "\ufeff日本語です。")
        self.assertEqual(load_surfaces(path)[0].text, "日本語です。")

    def test_surface_schema_is_strict(self):
        base = {
            "version": 1,
            "surfaces": [{"id": "body", "kind": "body", "markup": "plain", "text": "本文"}],
        }
        mutations = [
            lambda d: d.update(version=True),
            lambda d: d.update(unknown=True),
            lambda d: d.update(surfaces=[]),
            lambda d: d["surfaces"].append(deepcopy(d["surfaces"][0])),
            lambda d: d["surfaces"][0].update(text=""),
            lambda d: d["surfaces"][0].update(text=123),
            lambda d: d["surfaces"][0].update(markup="html"),
            lambda d: d["surfaces"][0].update(id="*"),
            lambda d: d["surfaces"][0].update(id=" body "),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                data = deepcopy(base)
                mutate(data)
                with self.assertRaises(ValueError):
                    parse_surfaces(data)

    def test_duplicate_json_keys_and_nonfinite_numbers_fail(self):
        for value in ('{"version":1,"version":2}', '{"value":NaN}', '{"value":Infinity}'):
            with self.subTest(value=value):
                path = self.write("bad.json", value)
                with self.assertRaises(ValueError):
                    read_json(path)

    def test_surfaces_json_cli(self):
        data = {
            "version": 1,
            "surfaces": [
                {"id": "title", "kind": "title", "markup": "plain", "text": "説明"},
                {"id": "note", "kind": "note", "markup": "plain", "text": "確認を行います。"},
            ],
        }
        path = self.write("surfaces.json", json.dumps(data, ensure_ascii=False))
        result = self.cli(str(path), "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["surface_count"], 2)
        self.assertEqual(report["findings"][0]["surface"], "note")

    def test_reference_cases_are_well_formed_not_a_translation_score(self):
        data = read_json(SEMANTIC_CASES)
        self.assertEqual(data["purpose"], "manual_semantic_review_not_automatic_scoring")
        cases = data["cases"]
        self.assertGreaterEqual(len(cases), 20)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["invariants"])
                self.assertTrue(case["acceptable"])
                self.assertTrue(case["unacceptable"])
                self.assertNotEqual(case["acceptable"], case["unacceptable"])

        by_id = {case["id"]: case for case in cases}
        for case_id in (
            "counts-and-subject",
            "prohibition",
            "partial-negation",
            "unconfirmed-schedule",
        ):
            self.assertIn(case_id, by_id)


if __name__ == "__main__":
    unittest.main()
