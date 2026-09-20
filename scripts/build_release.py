"""Build and verify a deterministic runtime-only skill release archive."""

from __future__ import annotations

import argparse
import ast
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import zipfile


SKILL_NAME = "natural-japanese-copilot"
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
EXCLUDED_DIRECTORY_NAMES = frozenset({"__pycache__", "docs", "tests"})
VERSION_PATTERN = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
)
FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
REGULAR_FILE_MODE = 0o100644


class UsageInputError(ValueError):
    """Invalid command-line or repository-root input."""


class ReleaseError(RuntimeError):
    """The requested release could not be built or verified."""


def validate_version(value: str) -> str:
    if len(value) > 32 or VERSION_PATTERN.fullmatch(value) is None:
        raise UsageInputError(
            "version must be canonical MAJOR.MINOR.PATCH digits without a leading 'v'"
        )
    return value


def parse_scalar(raw_value: str, context: str) -> str:
    value = raw_value.strip()
    if not value or value in {"|", ">"}:
        raise ReleaseError(f"{context} must be a nonempty scalar string")
    if value[:1] in {"'", '"'}:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as error:
            raise ReleaseError(f"cannot parse {context}: invalid quoting") from error
        if not isinstance(parsed, str) or not parsed:
            raise ReleaseError(f"{context} must be a nonempty scalar string")
        return parsed
    return value


def read_skill_metadata_version(skill_root: Path) -> str:
    path = skill_root.joinpath("SKILL.md")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ReleaseError(f"cannot read SKILL.md metadata.version: {error}") from error
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ReleaseError("cannot parse SKILL.md metadata.version: frontmatter is missing")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise ReleaseError(
            "cannot parse SKILL.md metadata.version: frontmatter is not closed"
        ) from error

    metadata_seen = False
    in_metadata = False
    versions: list[str] = []
    for line_number, line in enumerate(lines[1:closing], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[:1].isspace():
            match = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*):[ \t]*(.*)", line)
            if match is None:
                raise ReleaseError(
                    "cannot parse SKILL.md metadata.version: "
                    f"invalid frontmatter line {line_number}"
                )
            key, raw_value = match.groups()
            in_metadata = key == "metadata"
            if in_metadata:
                if metadata_seen:
                    raise ReleaseError(
                        "cannot parse SKILL.md metadata.version: duplicate metadata"
                    )
                metadata_seen = True
                if raw_value.strip():
                    raise ReleaseError(
                        "cannot parse SKILL.md metadata.version: metadata must be a mapping"
                    )
            continue
        if not in_metadata:
            continue
        nested = re.fullmatch(
            r"([A-Za-z][A-Za-z0-9_-]*):[ \t]*(.*)",
            line.lstrip(),
        )
        if nested is None:
            raise ReleaseError(
                "cannot parse SKILL.md metadata.version: "
                f"invalid metadata line {line_number}"
            )
        key, raw_value = nested.groups()
        if key == "version":
            versions.append(
                parse_scalar(raw_value, "SKILL.md metadata.version")
            )
    if len(versions) != 1:
        raise ReleaseError(
            "cannot parse SKILL.md metadata.version: "
            "exactly one metadata.version value is required"
        )
    version = versions[0]
    if VERSION_PATTERN.fullmatch(version) is None:
        raise ReleaseError(
            "SKILL.md metadata.version must be canonical MAJOR.MINOR.PATCH"
        )
    return version


def read_runtime_version(skill_root: Path) -> str:
    path = skill_root.joinpath("scripts", "review_japanese.py")
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ReleaseError(f"cannot read runtime checker VERSION: {error}") from error
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        raise ReleaseError(
            f"cannot parse runtime checker VERSION: {error.msg}"
        ) from error
    assignments: list[ast.expr | None] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "VERSION"
            for target in node.targets
        ):
            assignments.append(node.value)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "VERSION"
        ):
            assignments.append(node.value)
    if len(assignments) != 1:
        raise ReleaseError(
            "cannot parse runtime checker VERSION: "
            "exactly one top-level assignment is required"
        )
    value = assignments[0]
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        raise ReleaseError(
            "cannot parse runtime checker VERSION: a string literal is required"
        )
    version = value.value
    if VERSION_PATTERN.fullmatch(version) is None:
        raise ReleaseError(
            "runtime checker VERSION must be canonical MAJOR.MINOR.PATCH"
        )
    return version


def validate_release_version(skill_root: Path, requested_version: str) -> None:
    skill_version = read_skill_metadata_version(skill_root)
    runtime_version = read_runtime_version(skill_root)
    if len({requested_version, skill_version, runtime_version}) != 1:
        raise ReleaseError(
            "version mismatch: "
            f"--version={requested_version!r}, "
            f"SKILL.md metadata.version={skill_version!r}, "
            f"runtime VERSION={runtime_version!r}"
        )


def release_paths(root: Path, version: str) -> tuple[Path, Path, Path]:
    dist = root.joinpath("dist")
    archive = dist.joinpath(f"{SKILL_NAME}-v{version}.zip")
    checksums = dist.joinpath("SHA256SUMS")
    return dist, archive, checksums


def is_excluded(relative: PurePosixPath) -> bool:
    return any(
        part.startswith(".") or part in EXCLUDED_DIRECTORY_NAMES
        for part in relative.parts
    )


def collect_release_files(skill_root: Path) -> list[tuple[str, Path]]:
    if not skill_root.is_dir() or skill_root.is_symlink():
        raise ReleaseError(f"skill directory is missing or unsafe: {skill_root}")
    actual: dict[str, Path] = {}
    try:
        paths = sorted(skill_root.rglob("*"), key=lambda path: path.as_posix())
    except OSError as error:
        raise ReleaseError(f"cannot enumerate skill directory: {error}") from error
    for path in paths:
        relative = PurePosixPath(path.relative_to(skill_root).as_posix())
        if is_excluded(relative):
            continue
        if path.is_symlink():
            raise ReleaseError(f"release input must not be a symbolic link: {relative}")
        if not path.is_file():
            continue
        name = relative.as_posix()
        if name not in RELEASE_FILE_ALLOWLIST:
            raise ReleaseError(f"release input is not allowlisted: {name}")
        actual[name] = path
    missing = sorted(RELEASE_FILE_ALLOWLIST - actual.keys())
    if missing:
        raise ReleaseError(
            "release input is incomplete; missing: " + ", ".join(missing)
        )
    return sorted(actual.items())


def ensure_safe_output(path: Path) -> None:
    if path.is_symlink():
        raise ReleaseError(f"refusing to replace symbolic-link output: {path}")
    if path.exists() and not path.is_file():
        raise ReleaseError(f"refusing to replace non-file output: {path}")


def prepare_dist(root: Path, version: str) -> tuple[Path, Path, Path]:
    dist, archive, checksums = release_paths(root, version)
    if dist.is_symlink():
        raise ReleaseError(f"dist must not be a symbolic link: {dist}")
    if dist.exists() and not dist.is_dir():
        raise ReleaseError(f"dist is not a directory: {dist}")
    try:
        dist.mkdir(parents=False, exist_ok=True)
    except OSError as error:
        raise ReleaseError(f"cannot create dist directory: {error}") from error
    ensure_safe_output(archive)
    ensure_safe_output(checksums)
    return dist, archive, checksums


def write_archive(destination: Path, files: list[tuple[str, Path]]) -> None:
    try:
        with zipfile.ZipFile(
            destination,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=True,
        ) as archive:
            for relative, path in files:
                try:
                    data = path.read_bytes()
                except OSError as error:
                    raise ReleaseError(f"cannot read release input {relative}: {error}") from error
                archive_name = f"{SKILL_NAME}/{relative}"
                info = zipfile.ZipInfo(archive_name, date_time=FIXED_ZIP_TIMESTAMP)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = REGULAR_FILE_MODE << 16
                archive.writestr(
                    info,
                    data,
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
    except ReleaseError:
        raise
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as error:
        raise ReleaseError(f"cannot write release archive: {error}") from error


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as error:
        raise ReleaseError(f"cannot hash {path.name}: {error}") from error
    return digest.hexdigest()


def inspect_archive(
    archive_path: Path,
    files: list[tuple[str, Path]],
    *,
    compare_source: bool,
) -> None:
    expected_names = [f"{SKILL_NAME}/{relative}" for relative, _ in files]
    try:
        with zipfile.ZipFile(archive_path, mode="r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if names != expected_names:
                raise ReleaseError(
                    "archive manifest differs from the release allowlist"
                )
            if len(names) != len(set(names)):
                raise ReleaseError("archive contains duplicate paths")
            damaged = archive.testzip()
            if damaged is not None:
                raise ReleaseError(f"archive CRC check failed: {damaged}")
            source_by_name = {
                f"{SKILL_NAME}/{relative}": path for relative, path in files
            }
            for info in infos:
                pure_name = PurePosixPath(info.filename)
                if (
                    info.is_dir()
                    or pure_name.is_absolute()
                    or ".." in pure_name.parts
                    or pure_name.parts[0] != SKILL_NAME
                ):
                    raise ReleaseError(f"archive has unsafe path: {info.filename}")
                if info.date_time != FIXED_ZIP_TIMESTAMP:
                    raise ReleaseError(
                        f"archive timestamp is not deterministic: {info.filename}"
                    )
                if info.create_system != 3:
                    raise ReleaseError(
                        f"archive platform metadata is not deterministic: {info.filename}"
                    )
                if info.external_attr >> 16 != REGULAR_FILE_MODE:
                    raise ReleaseError(
                        f"archive mode is not deterministic: {info.filename}"
                    )
                if compare_source:
                    try:
                        source = source_by_name[info.filename].read_bytes()
                    except OSError as error:
                        raise ReleaseError(
                            f"cannot compare source for {info.filename}: {error}"
                        ) from error
                    if archive.read(info) != source:
                        raise ReleaseError(
                            f"archive content differs from source: {info.filename}"
                        )
    except ReleaseError:
        raise
    except (OSError, KeyError, RuntimeError, zipfile.BadZipFile) as error:
        raise ReleaseError(f"cannot verify release archive: {error}") from error


def verify_release(root: Path, version: str) -> str:
    skill_root = root.joinpath("skills", SKILL_NAME)
    validate_release_version(skill_root, version)
    _, archive, checksums = release_paths(root, version)
    ensure_safe_output(archive)
    ensure_safe_output(checksums)
    if not archive.is_file():
        raise ReleaseError(f"release archive is missing: {archive}")
    if not checksums.is_file():
        raise ReleaseError(f"checksum file is missing: {checksums}")
    files = collect_release_files(skill_root)
    inspect_archive(archive, files, compare_source=True)
    digest = sha256_file(archive)
    expected = f"{digest}  {archive.name}\n"
    try:
        actual = checksums.read_text(encoding="ascii")
    except (OSError, UnicodeError) as error:
        raise ReleaseError(f"cannot read checksum file: {error}") from error
    if actual != expected:
        raise ReleaseError("SHA256SUMS does not match the release archive")
    return digest


def temporary_path(dist: Path, label: str) -> Path:
    try:
        handle = tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{label}-",
            suffix=".tmp",
            dir=dist,
            delete=False,
        )
    except OSError as error:
        raise ReleaseError(f"cannot create temporary output in dist: {error}") from error
    path = Path(handle.name)
    handle.close()
    return path


def build_release(root: Path, version: str) -> tuple[Path, Path, str]:
    skill_root = root.joinpath("skills", SKILL_NAME)
    validate_release_version(skill_root, version)
    files = collect_release_files(skill_root)
    dist, archive, checksums = prepare_dist(root, version)
    temporary_archive: Path | None = None
    temporary_checksums: Path | None = None
    try:
        temporary_archive = temporary_path(dist, "archive")
        temporary_checksums = temporary_path(dist, "checksums")
        write_archive(temporary_archive, files)
        inspect_archive(temporary_archive, files, compare_source=True)
        digest = sha256_file(temporary_archive)
        checksum_text = f"{digest}  {archive.name}\n"
        try:
            temporary_checksums.write_text(
                checksum_text,
                encoding="ascii",
                newline="\n",
            )
        except OSError as error:
            raise ReleaseError(f"cannot write checksum file: {error}") from error
        try:
            os.replace(temporary_archive, archive)
            os.replace(temporary_checksums, checksums)
        except OSError as error:
            raise ReleaseError(f"cannot replace release outputs safely: {error}") from error
    finally:
        for path in (temporary_archive, temporary_checksums):
            if path is None:
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
    verified_digest = verify_release(root, version)
    if verified_digest != digest:
        raise ReleaseError("release digest changed during publication")
    return archive, checksums, digest


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="release version, for example 0.1.0")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of this script directory)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="verify existing outputs instead of rebuilding them",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    try:
        version = validate_version(args.version)
        root = args.root.resolve()
        if not root.is_dir():
            raise UsageInputError(f"repository root is not a directory: {root}")
    except UsageInputError as error:
        print(f"release input error: {error}", file=sys.stderr)
        return 2
    try:
        if args.verify_only:
            digest = verify_release(root, version)
            archive = release_paths(root, version)[1]
            print(f"release verification passed: {archive}")
            print(f"sha256: {digest}")
        else:
            archive, checksums, digest = build_release(root, version)
            print(f"release archive: {archive}")
            print(f"checksums: {checksums}")
            print(f"sha256: {digest}")
    except (ReleaseError, OSError) as error:
        action = "verification" if args.verify_only else "build"
        print(f"release {action} failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
