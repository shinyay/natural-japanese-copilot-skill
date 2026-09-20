"""Read-only Japanese prose hints and explicit literal-contract checks."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any


VERSION = "0.1.0"


@dataclass(frozen=True)
class Surface:
    id: str
    kind: str
    markup: str
    text: str


@dataclass(frozen=True)
class LiteralCheck:
    id: str
    surface: str
    source_excerpt: str
    allowed: tuple[str, ...]
    min_count: int
    max_count: int | None


@dataclass(frozen=True)
class Contract:
    expected_surface_ids: tuple[str, ...]
    checks: tuple[LiteralCheck, ...]


JAPANESE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)")
PROFILES = ("business", "technical", "slides", "ui")
STYLE_RULES = (
    (
        "indirect-capability",
        re.compile(r"することが(?:できます|可能です|可能となります)"),
        "「できます」などで簡潔にできるか確認します。能力の意味は残してください。",
    ),
    (
        "nominalized-action",
        re.compile(r"(?:確認|変更|検討|説明|設定)を(?:行います|行う|実施します|実施する)"),
        "動詞で直接表せるか確認します。行為名を示す必要がある場合は残します。",
    ),
    (
        "uncertainty-ending",
        re.compile(r"と(?:言|い)えるでしょう|ではないでしょうか"),
        "実際の不確実性や問いかけなら残します。単なる語尾の変化なら見直します。",
    ),
    (
        "vague-emphasis",
        re.compile(r"重要な役割を果た|可能性を秘め|新たな地平"),
        "何を意味するか具体的に伝わるか確認します。根拠や数値を創作しないでください。",
    ),
    (
        "empty-framing",
        re.compile(r"いかがでした(?:でしょう)?か|以下では[^。\n]{0,50}詳しく解説します"),
        "読者に必要な案内か確認します。翻訳では無断で省略しないでください。",
    ),
)


def require_object(
    value: Any, keys: set[str], context: str
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{context}: object required")
    missing = keys - value.keys()
    unknown = value.keys() - keys
    if missing or unknown:
        raise ValueError(
            f"{context}: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    return value


def require_string(value: Any, context: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ValueError(f"{context}: {'string' if allow_empty else 'nonempty string'} required")
    if "\x00" in value:
        raise ValueError(f"{context}: NUL bytes are not supported")
    return value


def require_version(value: Any, context: str) -> None:
    if type(value) is not int or value != 1:
        raise ValueError(f"{context}: version must be 1")


def require_id(value: Any, context: str) -> str:
    result = require_string(value, context)
    if result != result.strip() or result == "*":
        raise ValueError(f"{context}: whitespace around IDs and '*' are reserved")
    return result


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def invalid_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def read_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    if "\x00" in text:
        raise ValueError(f"{path}: binary/NUL input is not supported")
    return text


def read_json(path: Path) -> Any:
    return json.loads(
        read_text(path),
        object_pairs_hook=unique_object,
        parse_constant=invalid_constant,
    )


def parse_surfaces(data: Any) -> list[Surface]:
    root = require_object(data, {"version", "surfaces"}, "document")
    require_version(root["version"], "document")
    if not isinstance(root["surfaces"], list) or not root["surfaces"]:
        raise ValueError("document.surfaces: nonempty array required")
    surfaces: list[Surface] = []
    seen: set[str] = set()
    for index, item in enumerate(root["surfaces"]):
        context = f"surfaces[{index}]"
        row = require_object(item, {"id", "kind", "markup", "text"}, context)
        surface_id = require_id(row["id"], f"{context}.id")
        if surface_id in seen:
            raise ValueError(f"{context}: duplicate surface ID {surface_id}")
        seen.add(surface_id)
        kind = require_string(row["kind"], f"{context}.kind")
        if row["markup"] not in ("plain", "markdown"):
            raise ValueError(f"{context}.markup: use plain or markdown")
        text = require_string(row["text"], f"{context}.text", allow_empty=True)
        surfaces.append(Surface(surface_id, kind, row["markup"], text))
    if not any(surface.text.strip() for surface in surfaces):
        raise ValueError("document: all surfaces are empty")
    return surfaces


def load_surfaces(path: Path) -> list[Surface]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return parse_surfaces(read_json(path))
    if suffix not in (".md", ".txt"):
        raise ValueError("supported input extensions: .md, .txt, .json")
    text = require_string(read_text(path), str(path))
    return [Surface("body", "body", "markdown" if suffix == ".md" else "plain", text)]


def parse_contract(data: Any) -> Contract:
    root = require_object(
        data, {"version", "expected_surface_ids", "checks"}, "contract"
    )
    require_version(root["version"], "contract")
    expected_raw = root["expected_surface_ids"]
    if not isinstance(expected_raw, list) or not expected_raw:
        raise ValueError("contract.expected_surface_ids: nonempty array required")
    expected = tuple(
        require_id(value, "contract.expected_surface_ids") for value in expected_raw
    )
    if len(set(expected)) != len(expected):
        raise ValueError("contract.expected_surface_ids: duplicate ID")
    if not isinstance(root["checks"], list) or not root["checks"]:
        raise ValueError("contract.checks: nonempty array required")
    checks: list[LiteralCheck] = []
    seen: set[str] = set()
    keys = {"id", "surface", "source_excerpt", "allowed", "min_count", "max_count"}
    for index, item in enumerate(root["checks"]):
        context = f"checks[{index}]"
        row = require_object(item, keys, context)
        check_id = require_id(row["id"], f"{context}.id")
        if check_id in seen:
            raise ValueError(f"{context}: duplicate check ID {check_id}")
        seen.add(check_id)
        surface_id = require_string(row["surface"], f"{context}.surface")
        if surface_id != "*" and surface_id not in expected:
            raise ValueError(f"{context}.surface: ID not in expected_surface_ids")
        source_excerpt = require_string(row["source_excerpt"], f"{context}.source_excerpt")
        if not isinstance(row["allowed"], list) or not row["allowed"]:
            raise ValueError(f"{context}.allowed: nonempty array required")
        allowed = tuple(
            require_string(value, f"{context}.allowed") for value in row["allowed"]
        )
        if len(set(allowed)) != len(allowed):
            raise ValueError(f"{context}.allowed: duplicate string")
        minimum, maximum = row["min_count"], row["max_count"]
        if type(minimum) is not int or minimum < 0:
            raise ValueError(f"{context}.min_count: nonnegative integer required")
        if maximum is not None and (
            type(maximum) is not int or maximum < minimum
        ):
            raise ValueError(f"{context}.max_count: null or integer >= min_count required")
        checks.append(
            LiteralCheck(check_id, surface_id, source_excerpt, allowed, minimum, maximum)
        )
    return Contract(expected, tuple(checks))


def blank(text: str) -> str:
    return "".join(char if char in "\r\n" else " " for char in text)


def mask_markdown(text: str) -> str:
    lines: list[str] = []
    fence_char = ""
    fence_length = 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        if fence_char:
            lines.append(blank(line))
            if re.fullmatch(
                rf" {{0,3}}{re.escape(fence_char)}{{{fence_length},}}[ \t]*", content
            ):
                fence_char = ""
            continue
        opening = FENCE.match(line)
        if opening and not (
            opening.group(1).startswith("`") and "`" in opening.group(2)
        ):
            fence_char = opening.group(1)[0]
            fence_length = len(opening.group(1))
            lines.append(blank(line))
        elif re.match(r"^ {0,3}>", line):
            lines.append(blank(line))
        else:
            lines.append(line)
    masked = "".join(lines)
    masked = re.sub(
        r"<!--.*?(?:-->|\Z)", lambda match: blank(match.group()), masked, flags=re.S
    )
    code_pattern = r"(?<!`)(`+)(?!`)[\s\S]*?(?<!`)\1(?!`)"
    masked = re.sub(code_pattern, lambda match: blank(match.group()), masked)
    masked = re.sub(
        r"\]\([^)\r\n]*\)",
        lambda match: "]" + blank(match.group()[1:]),
        masked,
    )
    masked = re.sub(
        r"https?://[^\s<>]+", lambda match: blank(match.group()), masked
    )
    masked = re.sub(
        r"</?[A-Za-z][^>\r\n]*>", lambda match: blank(match.group()), masked
    )
    return masked


def location(text: str, offset: int) -> dict[str, int]:
    return {
        "line": text.count("\n", 0, offset) + 1,
        "column": offset - text.rfind("\n", 0, offset),
    }


def review_style(
    surfaces: list[Surface], profile: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for surface in surfaces:
        excluded_kind = surface.kind in ("code", "quote")
        prose = (
            blank(surface.text)
            if excluded_kind
            else mask_markdown(surface.text)
            if surface.markup == "markdown"
            else surface.text
        )
        coverage.append(
            {
                "surface": surface.id,
                "kind": surface.kind,
                "characters": len(surface.text),
                "masked_characters": sum(a != b for a, b in zip(surface.text, prose)),
                "japanese_characters": len(JAPANESE.findall(prose)),
                "style_excluded": excluded_kind,
            }
        )
        for rule_id, pattern, message in STYLE_RULES:
            for match in pattern.finditer(prose):
                findings.append(
                    {
                        "rule": rule_id,
                        "severity": "hint",
                        "surface": surface.id,
                        **location(prose, match.start()),
                        "excerpt": match.group(),
                        "message": message,
                    }
                )
        if profile in ("business", "technical"):
            for match in re.finditer(r"[^。！？!?\r\n]+[。！？!?]?", prose):
                sentence = " ".join(match.group().split())
                if len(sentence) > 120 and JAPANESE.search(sentence):
                    findings.append(
                        {
                            "rule": "long-sentence",
                            "severity": "hint",
                            "surface": surface.id,
                            **location(prose, match.start()),
                            "excerpt": sentence[:80],
                            "message": "120字を超える文です。条件や修飾の関係が分かるか確認します。",
                        }
                    )
    return findings, coverage


def review_contract(
    surfaces: list[Surface], contract: Contract
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    by_id = {surface.id: surface for surface in surfaces}
    expected = set(contract.expected_surface_ids)
    for missing in sorted(expected - by_id.keys()):
        findings.append(
            {"rule": "missing-surface", "severity": "error", "surface": missing}
        )
    for extra in sorted(by_id.keys() - expected):
        findings.append(
            {"rule": "unexpected-surface", "severity": "error", "surface": extra}
        )
    for check in contract.checks:
        if check.surface != "*" and check.surface not in by_id:
            results.append(
                {"id": check.id, "surface": check.surface, "status": "surface_missing"}
            )
            continue
        targets = surfaces if check.surface == "*" else [by_id[check.surface]]
        pattern = re.compile(
            "|".join(re.escape(value) for value in sorted(check.allowed, key=len, reverse=True))
        )
        matches: Counter[str] = Counter()
        for surface in targets:
            matches.update(match.group() for match in pattern.finditer(surface.text))
        count = sum(matches.values())
        matched = count >= check.min_count and (
            check.max_count is None or count <= check.max_count
        )
        result = {
            **asdict(check),
            "found_count": count,
            "matches": dict(matches),
            "status": "matched" if matched else "mismatch",
        }
        results.append(result)
        if not matched:
            findings.append(
                {
                    "rule": "protected-string-count",
                    "severity": "error",
                    "surface": check.surface,
                    "check": check.id,
                    "found_count": count,
                    "min_count": check.min_count,
                    "max_count": check.max_count,
                }
            )
    return findings, results


def review(
    surfaces: list[Surface], contract: Contract | None = None, profile: str = "business"
) -> dict[str, Any]:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}")
    if not surfaces or not any(surface.text.strip() for surface in surfaces):
        raise ValueError("nonempty document required")
    if len({surface.id for surface in surfaces}) != len(surfaces):
        raise ValueError("duplicate surface ID")
    style_findings, coverage = review_style(surfaces, profile)
    contract_findings, check_results = (
        review_contract(surfaces, contract) if contract is not None else ([], [])
    )
    return {
        "version": 1,
        "tool_version": VERSION,
        "profile": profile,
        "contract_status": (
            "not_run"
            if contract is None
            else "mismatch"
            if contract_findings
            else "matched"
        ),
        "style_status": (
            "reviewed" if any(item["japanese_characters"] for item in coverage)
            else "not_applicable"
        ),
        "semantic_review": "not_performed",
        "surface_count": len(surfaces),
        "style_hint_count": len(style_findings),
        "contract_error_count": len(contract_findings),
        "coverage": coverage,
        "checks": check_results,
        "findings": contract_findings + style_findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("input", type=Path, help="UTF-8 .md, .txt, or surfaces .json")
    parser.add_argument("--contract", type=Path, help="explicit literal checks as JSON")
    parser.add_argument("--profile", choices=PROFILES, default="business")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        surfaces = load_surfaces(args.input)
        contract = parse_contract(read_json(args.contract)) if args.contract else None
        result = review(surfaces, contract, args.profile)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(2, f"入力エラー: {error}\n")
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"保護条件: {result['contract_status']} / "
            f"文体の候補: {result['style_hint_count']} / 意味の照合: 未実施"
        )
        for finding in result["findings"]:
            where = finding["surface"]
            if "line" in finding:
                where += f":{finding['line']}:{finding['column']}"
            detail = finding.get("message", finding.get("check", "対象面を確認してください。"))
            print(f"{where} [{finding['rule']}] {detail}")
        print("文字列検査の結果です。自然さや意味の正しさを保証するものではありません。")
    return 1 if result["contract_error_count"] else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
