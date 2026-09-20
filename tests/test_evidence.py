from __future__ import annotations

import json
from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[1]
EVIDENCE = REPOSITORY.joinpath(
    "docs", "evidence", "app-development-check.json"
)


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


class DevelopmentEvidenceTests(unittest.TestCase):
    def test_app_development_evidence_has_required_shape(self):
        data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
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


if __name__ == "__main__":
    unittest.main()
