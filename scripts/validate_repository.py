"""Validate the repository's publishable source tree using only the standard library."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Iterable


SKILL_NAME = "natural-japanese-copilot"
SKILL_RELATIVE = PurePosixPath("skills", SKILL_NAME)
FRONTMATTER_KEYS = ("name", "description", "license", "compatibility")

RELEASE_FILE_ALLOWLIST = frozenset(
    {
        "LICENSE",
        "SKILL.md",
        "assets/glossary-template.md",
        "assets/style-profile-template.md",
        "references/artifact-profiles.md",
        "references/japanese-style.md",
        "references/review.md",
        "references/semantic-cases.json",
        "references/translation.md",
        "scripts/review_japanese.py",
    }
)

REQUIRED_REPOSITORY_FILES = frozenset(
    {
        ".editorconfig",
        ".gitattributes",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/pull_request_template.md",
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
        ".gitignore",
        "CHANGELOG.md",
        "CONTRIBUTING.en.md",
        "CONTRIBUTING.md",
        "docs/evidence/app-development-check.json",
        "docs/evidence/app-v0.1.0-rc-check.json",
        "LICENSE",
        "README.en.md",
        "README.md",
        "SECURITY.en.md",
        "SECURITY.md",
        "examples/contract.json",
        "examples/copilot-instructions.md",
        "examples/README.en.md",
        "examples/README.md",
        "examples/source.txt",
        "examples/surfaces-contract.json",
        "examples/surfaces.json",
        "examples/translation-broken.md",
        "examples/translation.md",
        "scripts/build_release.py",
        "scripts/validate_repository.py",
        "tests/test_build_release.py",
        "tests/test_evidence.py",
        "tests/test_repository_configuration.py",
        "tests/test_review_japanese.py",
        "tests/test_validate_repository.py",
        *(f"{SKILL_RELATIVE.as_posix()}/{name}" for name in RELEASE_FILE_ALLOWLIST),
    }
)

OPTIONAL_ROOT_FILES = frozenset(
    {
        "CHANGELOG.md",
        "CODE_OF_CONDUCT.md",
        "SUPPORT.md",
    }
)
IGNORED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".idea",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".vscode",
        "__pycache__",
        "dist",
        "htmlcov",
    }
)
IGNORED_FILE_NAMES = frozenset(
    {
        ".coverage",
        ".DS_Store",
        "Thumbs.db",
    }
)
IGNORED_SUFFIXES = frozenset({".pyc", ".pyo", ".swp"})
TEXT_SUFFIXES = frozenset(
    {
        ".cfg",
        ".ini",
        ".json",
        ".md",
        ".py",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
)
TEXT_FILE_NAMES = frozenset(
    {
        ".editorconfig",
        ".gitattributes",
        ".gitignore",
        "LICENSE",
    }
)
DOC_IMAGE_SUFFIXES = frozenset({".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"})
TEST_SUFFIXES = frozenset({".json", ".md", ".py", ".txt"})
EXAMPLE_SUFFIXES = frozenset({".json", ".md", ".txt"})

FORBIDDEN_PUBLIC_ROOT_FILENAMES = frozenset(
    {
        "attribution.md",
        "upstream-license.txt",
    }
)
SESSION_MARKERS = (
    ".copilot/" + "session" + "-state",
    ".copilot\\" + "session" + "-state",
    "session" + "-state",
    "session_" + "context",
    "project_" + "session_id",
    "copilot_" + "session_id",
    "onedrive" + " - microsoft",
)
PERSONAL_PATH_PATTERNS = (
    re.compile(r"(?i)(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"'<>]+)"),
    re.compile(r"(?i)(?<![A-Za-z0-9])/(?:Users|home)/[^/\s\"'<>]+/"),
)
FRONTMATTER_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):[ \t]*(.*)$")
SEMANTIC_VERSION = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
)
RESOURCE_CODE = re.compile(
    r"`((?:references|assets|scripts)[\\/][^`\r\n<>]+)`"
)
MARKDOWN_LINK = re.compile(r"!?\[[^\]\r\n]*\]\(([^)\r\n]+)\)")


class RepositoryReadError(RuntimeError):
    """Raised when the tree cannot be read reliably."""


def normalize_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_ignored(relative: PurePosixPath) -> bool:
    if any(part in IGNORED_DIRECTORY_NAMES for part in relative.parts[:-1]):
        return True
    name = relative.name
    if name in IGNORED_FILE_NAMES or name.startswith(".coverage."):
        return True
    return relative.suffix.lower() in IGNORED_SUFFIXES


def iter_public_files(root: Path) -> Iterable[tuple[PurePosixPath, Path]]:
    try:
        paths = sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold())
    except OSError as error:
        raise RepositoryReadError(f"cannot enumerate repository: {error}") from error
    for path in paths:
        relative = PurePosixPath(normalize_relative(path, root))
        if is_ignored(relative):
            continue
        try:
            if path.is_symlink():
                yield relative, path
            elif path.is_file():
                yield relative, path
        except OSError as error:
            raise RepositoryReadError(f"cannot inspect {relative}: {error}") from error


def is_allowed_public_path(relative: PurePosixPath) -> bool:
    parts = relative.parts
    if not parts:
        return False
    if len(parts) == 1:
        return (
            relative.as_posix() in REQUIRED_REPOSITORY_FILES
            or relative.name in OPTIONAL_ROOT_FILES
        )
    top = parts[0]
    suffix = relative.suffix.lower()
    if top == ".github":
        if len(parts) == 2 and parts[1] in {
            "CODEOWNERS",
            "PULL_REQUEST_TEMPLATE.md",
            "pull_request_template.md",
            "dependabot.yml",
        }:
            return True
        if len(parts) >= 3 and parts[1] == "ISSUE_TEMPLATE":
            return suffix in {".md", ".yaml", ".yml"}
        return len(parts) == 3 and parts[1] == "workflows" and suffix in {
            ".yaml",
            ".yml",
        }
    if top == "docs":
        if len(parts) >= 3 and parts[1] in {"en", "ja"}:
            return suffix == ".md"
        if len(parts) >= 3 and parts[1] == "evidence":
            return suffix == ".json"
        if len(parts) >= 3 and parts[1] == "images":
            return suffix in DOC_IMAGE_SUFFIXES
        return False
    if top == "examples":
        return len(parts) == 2 and suffix in EXAMPLE_SUFFIXES
    if top == "scripts":
        return len(parts) == 2 and suffix == ".py"
    if top == "tests":
        return suffix in TEST_SUFFIXES
    if top == "skills":
        return (
            len(parts) >= 3
            and parts[1] == SKILL_NAME
            and PurePosixPath(*parts[2:]).as_posix() in RELEASE_FILE_ALLOWLIST
        )
    return False


def validate_public_allowlist(
    files: Iterable[tuple[PurePosixPath, Path]],
) -> list[str]:
    errors: list[str] = []
    seen_casefold: dict[str, str] = {}
    for relative, path in files:
        display = relative.as_posix()
        folded = display.casefold()
        previous = seen_casefold.get(folded)
        if previous is not None and previous != display:
            errors.append(f"path case collision: {previous} and {display}")
        else:
            seen_casefold[folded] = display
        if path.is_symlink():
            errors.append(f"symbolic links are not publishable: {display}")
        if not is_allowed_public_path(relative):
            errors.append(f"path is not in the public allowlist: {display}")
    return errors


def validate_required_files(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in sorted(REQUIRED_REPOSITORY_FILES):
        path = root.joinpath(*PurePosixPath(relative).parts)
        if not path.is_file() or path.is_symlink():
            errors.append(f"required public file is missing: {relative}")
    return errors


def parse_frontmatter_scalar(raw_value: str, key: str) -> str:
    value = raw_value.strip()
    if value[:1] in {"'", '"'}:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as error:
            raise ValueError(
                f"SKILL.md frontmatter key {key!r} has invalid quoting"
            ) from error
        if not isinstance(parsed, str):
            raise ValueError(f"SKILL.md frontmatter key {key!r} must be a string")
        return parsed
    if value in {"|", ">"}:
        raise ValueError(
            f"SKILL.md frontmatter key {key!r} must have a scalar value"
        )
    return value


def parse_frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RepositoryReadError(f"cannot read {path.name}: {error}") from error
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise ValueError("SKILL.md frontmatter is not closed") from error
    values: dict[str, str] = {}
    parent_key: str | None = None
    for line_number, line in enumerate(lines[1:closing], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace():
            if parent_key is None:
                raise ValueError(
                    f"SKILL.md frontmatter line {line_number} has unexpected indentation"
                )
            nested = FRONTMATTER_KEY.fullmatch(line.lstrip())
            if nested is None:
                raise ValueError(
                    f"SKILL.md frontmatter line {line_number} must be a key/value"
                )
            nested_key, raw_value = nested.groups()
            key = f"{parent_key}.{nested_key}"
            if key in values:
                raise ValueError(f"SKILL.md frontmatter has duplicate key: {key}")
            values[key] = parse_frontmatter_scalar(raw_value, key)
            continue
        match = FRONTMATTER_KEY.fullmatch(line)
        if not match:
            raise ValueError(
                f"SKILL.md frontmatter line {line_number} must be a scalar key/value"
            )
        key, raw_value = match.groups()
        if key in values:
            raise ValueError(f"SKILL.md frontmatter has duplicate key: {key}")
        values[key] = parse_frontmatter_scalar(raw_value, key)
        parent_key = key if not raw_value.strip() else None
    return values


def validate_frontmatter(root: Path) -> list[str]:
    skill_root = root.joinpath(*SKILL_RELATIVE.parts)
    skill_file = skill_root.joinpath("SKILL.md")
    if not skill_file.is_file():
        return []
    try:
        values = parse_frontmatter(skill_file)
    except ValueError as error:
        return [str(error)]
    errors: list[str] = []
    for key in FRONTMATTER_KEYS:
        if not values.get(key, "").strip():
            errors.append(f"SKILL.md frontmatter is missing nonempty {key!r}")
    name = values.get("name", "")
    if name and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        errors.append("SKILL.md frontmatter name must use lowercase kebab-case")
    if name and name != skill_root.name:
        errors.append(
            "SKILL.md frontmatter name must match its directory "
            f"({name!r} != {skill_root.name!r})"
        )
    if name and name != SKILL_NAME:
        errors.append(f"SKILL.md frontmatter name must be {SKILL_NAME!r}")
    if values.get("license") and values["license"] != "MIT":
        errors.append("SKILL.md frontmatter license must be 'MIT'")
    return errors


def validate_version_contract(root: Path) -> list[str]:
    skill_root = root.joinpath(*SKILL_RELATIVE.parts)
    skill_file = skill_root.joinpath("SKILL.md")
    runtime_file = skill_root.joinpath("scripts", "review_japanese.py")
    if not skill_file.is_file() or not runtime_file.is_file():
        return []
    try:
        values = parse_frontmatter(skill_file)
    except ValueError:
        return []
    metadata_version = values.get("metadata.version", "")
    errors: list[str] = []
    if not metadata_version:
        errors.append("SKILL.md frontmatter metadata.version is required")
    elif SEMANTIC_VERSION.fullmatch(metadata_version) is None:
        errors.append(
            "SKILL.md frontmatter metadata.version must be canonical MAJOR.MINOR.PATCH"
        )
    try:
        source = runtime_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(runtime_file))
    except (OSError, UnicodeError) as error:
        raise RepositoryReadError(f"cannot read runtime checker: {error}") from error
    except SyntaxError as error:
        return [f"runtime checker cannot be parsed: {error.msg}"]

    versions: list[str] = []
    for node in tree.body:
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "VERSION"
            for target in node.targets
        ):
            value = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "VERSION"
        ):
            value = node.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            versions.append(value.value)
        elif value is not None:
            errors.append("runtime checker VERSION must be a string literal")
    if len(versions) != 1:
        errors.append("runtime checker must define exactly one literal VERSION")
    else:
        runtime_version = versions[0]
        if SEMANTIC_VERSION.fullmatch(runtime_version) is None:
            errors.append("runtime checker VERSION must be canonical MAJOR.MINOR.PATCH")
        if metadata_version and runtime_version != metadata_version:
            errors.append(
                "runtime checker VERSION must match SKILL.md metadata.version "
                f"({runtime_version!r} != {metadata_version!r})"
            )

    tool_version_uses_constant = any(
        isinstance(node, ast.Dict)
        and any(
            isinstance(key, ast.Constant)
            and key.value == "tool_version"
            and isinstance(value, ast.Name)
            and value.id == "VERSION"
            for key, value in zip(node.keys, node.values)
        )
        for node in ast.walk(tree)
    )
    if not tool_version_uses_constant:
        errors.append("runtime checker JSON tool_version must use VERSION")
    return errors


def validate_mit_licenses(root: Path) -> list[str]:
    errors: list[str] = []
    markers = (
        "MIT License",
        "Permission is hereby granted, free of charge",
        'THE SOFTWARE IS PROVIDED "AS IS"',
    )
    for relative in (
        PurePosixPath("LICENSE"),
        SKILL_RELATIVE.joinpath("LICENSE"),
    ):
        path = root.joinpath(*relative.parts)
        if not path.is_file() or path.is_symlink():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise RepositoryReadError(f"cannot read {relative}: {error}") from error
        if any(marker not in text for marker in markers):
            errors.append(f"MIT license text is incomplete: {relative.as_posix()}")
    return errors


def clean_link_target(raw: str) -> str | None:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if any(character.isspace() for character in target):
        target = target.split(None, 1)[0]
    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    if not target or target.startswith(("#", "/", "\\")):
        return None
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
        return None
    if "<" in target or ">" in target:
        return None
    return target.replace("\\", "/")


def resolve_inside(root: Path, base: Path, target: str) -> Path | None:
    candidate = base.joinpath(*PurePosixPath(target).parts).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return None
    return candidate


def validate_references(
    root: Path, files: Iterable[tuple[PurePosixPath, Path]]
) -> list[str]:
    errors: list[str] = []
    skill_root = root.joinpath(*SKILL_RELATIVE.parts)
    for relative, path in files:
        if path.suffix.lower() != ".md" or path.is_symlink():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise RepositoryReadError(f"cannot read {relative}: {error}") from error
        references: list[tuple[str, Path]] = []
        for match in MARKDOWN_LINK.finditer(text):
            target = clean_link_target(match.group(1))
            if target is not None:
                references.append((target, path.parent))
        if relative.parts[:2] == ("skills", SKILL_NAME):
            for match in RESOURCE_CODE.finditer(text):
                target = clean_link_target(match.group(1))
                if target is not None:
                    references.append((target, skill_root))
        for target, base in references:
            candidate = resolve_inside(root, base, target)
            if candidate is None:
                errors.append(
                    f"reference escapes the repository: {relative.as_posix()} -> {target}"
                )
            elif not candidate.exists():
                errors.append(
                    f"referenced resource is missing: {relative.as_posix()} -> {target}"
                )
    return errors


def markdown_files(directory: Path) -> set[str]:
    if not directory.is_dir():
        return set()
    return {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*.md")
        if path.is_file()
        and not path.is_symlink()
        and not any(part.startswith(".") for part in path.relative_to(directory).parts)
    }


def validate_document_pairs(root: Path) -> list[str]:
    english = markdown_files(root.joinpath("docs", "en"))
    japanese = markdown_files(root.joinpath("docs", "ja"))
    errors: list[str] = []
    if not english and not japanese:
        errors.append("docs/en and docs/ja must contain at least one Markdown pair")
        return errors
    for relative in sorted(english - japanese):
        errors.append(f"Japanese documentation counterpart is missing: {relative}")
    for relative in sorted(japanese - english):
        errors.append(f"English documentation counterpart is missing: {relative}")
    return errors


def read_text_file(path: Path, relative: PurePosixPath) -> str | None:
    if path.name not in TEXT_FILE_NAMES and path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RepositoryReadError(f"cannot read text file {relative}: {error}") from error


def validate_forbidden_content(
    files: Iterable[tuple[PurePosixPath, Path]],
) -> list[str]:
    errors: list[str] = []
    for relative, path in files:
        display = relative.as_posix()
        if (
            len(relative.parts) == 1
            and relative.name.casefold() in FORBIDDEN_PUBLIC_ROOT_FILENAMES
        ):
            errors.append(f"forbidden public-root source file: {display}")
        if path.is_symlink():
            continue
        text = read_text_file(path, relative)
        if text is None:
            continue
        folded = text.casefold()
        for marker in SESSION_MARKERS:
            if marker.casefold() in folded:
                errors.append(f"session or workstation metadata appears in: {display}")
                break
        if any(pattern.search(text) for pattern in PERSONAL_PATH_PATTERNS):
            errors.append(f"personal absolute path appears in: {display}")
    return errors


def validate_release_allowlist(root: Path) -> list[str]:
    skill_root = root.joinpath(*SKILL_RELATIVE.parts)
    if not skill_root.is_dir():
        return []
    errors: list[str] = []
    actual: set[str] = set()
    try:
        paths = sorted(skill_root.rglob("*"), key=lambda item: item.as_posix())
    except OSError as error:
        raise RepositoryReadError(f"cannot enumerate skill directory: {error}") from error
    for path in paths:
        relative_path = path.relative_to(skill_root)
        relative = PurePosixPath(relative_path.as_posix())
        if any(part in {"__pycache__", "tests", "docs"} for part in relative.parts):
            continue
        if any(part.startswith(".") for part in relative.parts):
            continue
        if path.is_file() or path.is_symlink():
            display = relative.as_posix()
            actual.add(display)
            if display not in RELEASE_FILE_ALLOWLIST:
                errors.append(f"skill file is not in the release allowlist: {display}")
    for missing in sorted(RELEASE_FILE_ALLOWLIST - actual):
        errors.append(f"release allowlist file is missing: {missing}")
    return errors


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    files = list(iter_public_files(root))
    errors: list[str] = []
    errors.extend(validate_public_allowlist(files))
    errors.extend(validate_required_files(root))
    errors.extend(validate_frontmatter(root))
    errors.extend(validate_version_contract(root))
    errors.extend(validate_mit_licenses(root))
    errors.extend(validate_references(root, files))
    errors.extend(validate_document_pairs(root))
    errors.extend(validate_forbidden_content(files))
    errors.extend(validate_release_allowlist(root))
    return sorted(set(errors))


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of this script directory)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    if not args.root.exists() or not args.root.is_dir():
        print(f"validation input error: repository root is not a directory: {args.root}", file=sys.stderr)
        return 2
    try:
        errors = validate_repository(args.root)
        file_count = sum(1 for _ in iter_public_files(args.root.resolve()))
    except RepositoryReadError as error:
        print(f"validation input error: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"validation input error: {error}", file=sys.stderr)
        return 2
    if errors:
        print(f"repository validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"repository validation passed ({file_count} public files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
