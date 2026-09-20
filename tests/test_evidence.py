from __future__ import annotations

import json
from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
EVIDENCE_FILES = (
    REPOSITORY.joinpath("docs", "evidence", "app-development-check.json"),
    REPOSITORY.joinpath("docs", "evidence", "app-v0.1.0-rc-check.json"),
)


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


class AppEvidenceTests(unittest.TestCase):
    def assert_evidence_shape(self, path: Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIs(type(data), dict)
        self.assertIs(type(data.get("schema_version")), int)
        self.assertEqual(data["schema_version"], 1)

        environment = data.get("environment")
        self.assertIs(type(environment), dict)
        for key in (
            "client",
            "client_version",
            "operating_system",
            "model",
            "session",
        ):
            with self.subTest(section="environment", key=key):
                self.assertTrue(nonempty_string(environment.get(key)))

        method = data.get("method")
        self.assertIs(type(method), dict)
        for key in ("prompt", "reviewer", "review", "automation"):
            with self.subTest(section="method", key=key):
                self.assertTrue(nonempty_string(method.get(key)))
        self.assertIs(type(method.get("files_changed_by_check")), bool)
        self.assertFalse(method["files_changed_by_check"])

        skill = data.get("skill")
        self.assertIs(type(skill), dict)
        self.assertTrue(nonempty_string(skill.get("selector_used")))
        self.assertEqual(skill.get("load_result"), "success")
        if path.name == "app-v0.1.0-rc-check.json":
            self.assertEqual(
                skill.get("selector_used"),
                "natural-japanese-copilot",
            )
            self.assertTrue(nonempty_string(skill.get("source_commit")))

        limits = data.get("limits")
        self.assertIs(type(limits), list)
        self.assertTrue(limits)
        self.assertTrue(all(nonempty_string(item) for item in limits))

        cases = data.get("cases")
        self.assertIs(type(cases), list)
        self.assertEqual(len(cases), 8)
        identifiers: set[str] = set()
        for index, case in enumerate(cases):
            with self.subTest(case=index):
                self.assertIs(type(case), dict)
                self.assertTrue(nonempty_string(case.get("id")))
                self.assertNotIn(case["id"], identifiers)
                identifiers.add(case["id"])
                self.assertTrue(nonempty_string(case.get("source")))
                self.assertTrue(nonempty_string(case.get("output")))
                self.assertNotEqual(case["source"], case["output"])
                invariants = case.get("invariants_reviewed")
                self.assertIs(type(invariants), list)
                self.assertTrue(invariants)
                self.assertTrue(
                    all(nonempty_string(item) for item in invariants)
                )
                self.assertEqual(case.get("result"), "preserved")

    def test_app_evidence_has_required_shape(self):
        for path in EVIDENCE_FILES:
            with self.subTest(path=path.name):
                self.assert_evidence_shape(path)


if __name__ == "__main__":
    unittest.main()
