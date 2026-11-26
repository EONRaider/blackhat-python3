"""Static dependency scanner for the book chapters.

The chapters in this repository are standalone scripts that mirror the book's
printed listings, so their third-party requirements are declared out-of-band in
``pyproject.toml`` as one PEP 735 dependency group per chapter. This tool keeps
the two in sync without importing or executing any book code: it parses every
``chapterNN/**/*.py`` file with :mod:`ast`, collects top-level import names and
compares them with the declared groups using the mapping in
``tools/deps_scan.toml``.

Subcommands:

``report``
    Print a Markdown table of each chapter's third-party packages, platform
    constraints and external (non-PyPI) requirements.

``check``
    Exit non-zero if any import is unmapped, any mapped distribution is missing
    from its chapter's group, or any declared distribution is never imported.
    With ``--import``, additionally import every third-party module that
    applies to the running interpreter, proving the synced environment works.

``requirements``
    Write pip-compatible ``requirements.txt`` (every default chapter group)
    and ``requirements/<group>.txt`` from the dependency groups. These carry
    the same version ranges as ``pyproject.toml``, not lockfile pins, so they
    only change when the manifest does. With ``--check``, report drift instead.

Usage::

    uv run python tools/deps_scan.py report
    uv run python tools/deps_scan.py check --import
    uv run python tools/deps_scan.py requirements
"""

from __future__ import annotations

import argparse
import ast
import importlib
import re
import sys
import tomllib
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_NAME = "tools/deps_scan.toml"
CHAPTER_GLOB = "chapter*"
_CHAPTER_RE = re.compile(r"^chapter(\d+)$")
_REQ_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
_PLATFORM_NAMES = {"win32": "Windows", "linux": "Linux", "darwin": "macOS"}


def normalize(name: str) -> str:
    """Normalize a distribution name as described in PEP 503.

    Args:
        name: A distribution name in any casing or separator style.

    Returns:
        The lower-cased name with runs of ``-``, ``_`` and ``.`` collapsed to ``-``.
    """
    return re.sub(r"[-_.]+", "-", name).lower()


def chapter_group(chapter_dir: str) -> str:
    """Map a chapter directory name to its default dependency group.

    Args:
        chapter_dir: A directory name such as ``chapter04``.

    Returns:
        The group name, e.g. ``ch04``.

    Raises:
        ValueError: If ``chapter_dir`` is not a chapter directory name.
    """
    match = _CHAPTER_RE.match(chapter_dir)
    if match is None:
        msg = f"not a chapter directory: {chapter_dir!r}"
        raise ValueError(msg)
    return f"ch{int(match.group(1)):02d}"


@dataclass(frozen=True)
class ModuleSpec:
    """How a top-level import name maps onto a PyPI distribution.

    Attributes:
        dist: Normalized distribution name that provides the module.
        platform: ``sys.platform`` value the distribution is limited to, if any.
            A leading ``!`` inverts it: ``"!win32"`` means every platform but Windows.
        group: Dependency group override; defaults to the importing chapter's group.
        min_python: Minimum ``(major, minor)`` at which the dependency applies.
        max_python: First ``(major, minor)`` at which the dependency no longer
            applies, an exclusive upper bound mirroring a
            ``python_version < 'X.Y'`` environment marker.
    """

    dist: str
    platform: str | None = None
    group: str | None = None
    min_python: tuple[int, int] | None = None
    max_python: tuple[int, int] | None = None

    def applies_here(self) -> bool:
        """Return whether this dependency is installed on the running interpreter."""
        if self.platform is not None:
            excluded = self.platform.startswith("!")
            if (sys.platform == self.platform.lstrip("!")) == excluded:
                return False
        if self.min_python is not None and sys.version_info[:2] < self.min_python:
            return False
        return self.max_python is None or sys.version_info[:2] < self.max_python


@dataclass(frozen=True)
class Config:
    """Parsed contents of ``tools/deps_scan.toml``.

    Attributes:
        modules: Import name to distribution mapping.
        external: Import names provided by non-PyPI software, with a description.
        exclude: Repository-relative file paths that are not scanned.
        declared_without_import: Per-group distributions exempt from the
            "declared but never imported" check.
        unresolved: Known-broken imports that no installable dependency
            satisfies, with the reason. ``check`` reports them as warnings on
            every run so they stay visible without failing CI.
    """

    modules: dict[str, ModuleSpec]
    external: dict[str, str]
    exclude: frozenset[str]
    declared_without_import: dict[str, frozenset[str]] = field(default_factory=dict)
    unresolved: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> Config:
        """Load and validate the scanner configuration.

        Args:
            path: Path to the TOML configuration file.

        Returns:
            The parsed configuration.

        Raises:
            ValueError: If a module entry is malformed.
        """
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        modules: dict[str, ModuleSpec] = {}
        for name, raw in data.get("modules", {}).items():
            if not isinstance(raw, dict) or "dist" not in raw:
                msg = f"[modules].{name} must be a table with a 'dist' key"
                raise ValueError(msg)
            min_python = raw.get("min_python")
            max_python = raw.get("max_python")
            modules[name] = ModuleSpec(
                dist=normalize(raw["dist"]),
                platform=raw.get("platform"),
                group=raw.get("group"),
                min_python=_parse_version(min_python) if min_python else None,
                max_python=_parse_version(max_python) if max_python else None,
            )
        exclude = frozenset(data.get("exclude", {}).get("files", []))
        allowed = {
            group: frozenset(normalize(d) for d in dists)
            for group, dists in data.get("declared_without_import", {}).items()
        }
        return cls(
            modules=modules,
            external=dict(data.get("external", {})),
            exclude=exclude,
            declared_without_import=allowed,
            unresolved=dict(data.get("unresolved", {})),
        )


def _parse_version(text: str) -> tuple[int, int]:
    """Parse a ``"major.minor"`` string into a tuple."""
    major, minor = text.split(".", 1)
    return int(major), int(minor)


def load_raw_groups(pyproject: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Read requirement strings per dependency group and uv's default groups.

    Args:
        pyproject: Path to ``pyproject.toml``.

    Returns:
        A pair of (group name to requirement strings, ``[tool.uv] default-groups``).
        ``{include-group = ...}`` entries are skipped.
    """
    data: dict[str, Any] = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    groups = {
        group: [e for e in entries if isinstance(e, str)]
        for group, entries in data.get("dependency-groups", {}).items()
    }
    defaults = data.get("tool", {}).get("uv", {}).get("default-groups", [])
    return groups, list(defaults)


def render_requirements(groups: dict[str, list[str]], selected: Sequence[str]) -> str:
    """Render a pip requirements file for the given dependency groups.

    Args:
        groups: Output of :func:`load_raw_groups`.
        selected: Groups to include, in order. Duplicate requirements are dropped.

    Returns:
        File contents, including a generated-file header.
    """
    seen: dict[str, None] = {}
    for group in selected:
        for requirement in groups[group]:
            seen.setdefault(requirement, None)
    header = (
        "# Generated from pyproject.toml by `python tools/deps_scan.py requirements`.\n"
        "# Do not edit by hand. Groups: " + ", ".join(selected) + "\n"
    )
    return header + "".join(f"{req}\n" for req in seen)


def requirements_files(pyproject: Path) -> dict[str, str]:
    """Compute every generated requirements file and its contents.

    Args:
        pyproject: Path to ``pyproject.toml``.

    Returns:
        Mapping of repository-relative path to file contents.
    """
    groups, defaults = load_raw_groups(pyproject)
    chapters = [g for g in groups if g != "dev"]
    files = {"requirements.txt": render_requirements(groups, [g for g in defaults if g != "dev"])}
    for group in chapters:
        files[f"requirements/{group}.txt"] = render_requirements(groups, [group])
    return files


def sync_requirements(root: Path, *, check_only: bool) -> list[Problem]:
    """Write the generated requirements files, or report which ones drifted.

    Stale ``requirements/*.txt`` files for groups that no longer exist are
    removed (or reported when ``check_only`` is set).

    Args:
        root: Repository root.
        check_only: Report drift instead of writing files.

    Returns:
        Problems describing out-of-date files; always empty when writing.
    """
    wanted = requirements_files(root / "pyproject.toml")
    existing = {p.relative_to(root).as_posix() for p in root.glob("requirements/*.txt")}
    problems: list[Problem] = []
    for rel in sorted(existing - wanted.keys()):
        if check_only:
            problems.append(Problem(rel, "stale file; no matching dependency group"))
        else:
            (root / rel).unlink()
    for rel, content in wanted.items():
        path = root / rel
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            continue
        if check_only:
            problems.append(Problem(rel, "out of date; run `tools/deps_scan.py requirements`"))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    return problems


def load_groups(pyproject: Path) -> dict[str, set[str]]:
    """Read PEP 735 dependency groups and return normalized distribution names.

    Args:
        pyproject: Path to ``pyproject.toml``.

    Returns:
        Mapping of group name to the set of distributions it declares.
        ``{include-group = ...}`` entries are ignored.
    """
    data: dict[str, Any] = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    groups: dict[str, set[str]] = {}
    for group, entries in data.get("dependency-groups", {}).items():
        names: set[str] = set()
        for entry in entries:
            if isinstance(entry, str) and (match := _REQ_NAME_RE.match(entry)):
                names.add(normalize(match.group(1)))
        groups[group] = names
    return groups


@dataclass
class FileImports:
    """Top-level import names found in one source file.

    Attributes:
        path: Repository-relative POSIX path of the file.
        chapter: Chapter directory name the file belongs to.
        names: Top-level module names imported with absolute imports.
        error: Parse error message, if the file could not be parsed.
    """

    path: str
    chapter: str
    names: set[str] = field(default_factory=set)
    error: str | None = None


def iter_chapter_files(root: Path, exclude: Iterable[str] = ()) -> Iterator[Path]:
    """Yield every Python file under the chapter directories, sorted.

    Args:
        root: Repository root.
        exclude: Repository-relative POSIX paths to skip.

    Yields:
        Absolute paths of chapter source files.
    """
    skip = set(exclude)
    for path in sorted(root.glob(f"{CHAPTER_GLOB}/**/*.py")):
        if path.relative_to(root).as_posix() not in skip:
            yield path


def local_module_names(root: Path) -> set[str]:
    """Return names that resolve to sibling modules or packages inside the chapters.

    Args:
        root: Repository root.

    Returns:
        File stems and directory names found under the chapter directories.
    """
    names: set[str] = set()
    for path in root.glob(f"{CHAPTER_GLOB}/**/*"):
        names.add(path.stem if path.suffix == ".py" else path.name)
    return names


def extract_imports(source: bytes | str) -> set[str]:
    """Return the top-level names of all absolute imports in ``source``.

    Relative imports (``from . import x``) are ignored because they always
    refer to code inside the repository.

    Args:
        source: Python source code.

    Returns:
        Set of top-level module names, e.g. ``{"scapy", "os"}``.

    Raises:
        SyntaxError: If ``source`` is not valid Python 3 syntax.
    """
    with warnings.catch_warnings():
        # Book code contains invalid escape sequences; parsing must stay quiet.
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(source)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".", 1)[0])
    return found


def scan(root: Path, config: Config) -> list[FileImports]:
    """Collect third-party and external import names for each chapter file.

    Standard-library and repository-local names are dropped, except that a name
    listed in ``[modules]`` or ``[unresolved]`` is always kept. This keeps stdlib
    modules that were removed in newer Python versions (e.g. ``crypt``) visible
    on every interpreter so results do not depend on the running Python, and a
    chapter file that happens to share an unresolved name cannot hide the
    warning for an import elsewhere.

    Args:
        root: Repository root.
        config: Scanner configuration.

    Returns:
        One entry per scanned file, in path order.
    """
    stdlib = set(sys.stdlib_module_names)
    local = local_module_names(root)
    results: list[FileImports] = []
    for path in iter_chapter_files(root, config.exclude):
        rel = path.relative_to(root)
        entry = FileImports(path=rel.as_posix(), chapter=rel.parts[0])
        try:
            names = extract_imports(path.read_bytes())
        except SyntaxError as exc:
            entry.error = f"line {exc.lineno}: {exc.msg}"
        else:
            keep = config.modules.keys() | config.unresolved.keys()
            entry.names = {n for n in names if n in keep or (n not in stdlib and n not in local)}
        results.append(entry)
    return results


@dataclass(frozen=True)
class Problem:
    """A single consistency problem reported by :func:`check`."""

    location: str
    message: str

    def __str__(self) -> str:
        """Render as ``location: message``."""
        return f"{self.location}: {self.message}"


def check(
    results: Sequence[FileImports], config: Config, groups: dict[str, set[str]]
) -> list[Problem]:
    """Cross-check scanned imports against the declared dependency groups.

    Args:
        results: Output of :func:`scan`.
        config: Scanner configuration.
        groups: Output of :func:`load_groups`.

    Returns:
        All problems found, empty if the manifest is consistent.
    """
    problems: list[Problem] = []
    used: dict[str, set[str]] = defaultdict(set)
    for entry in results:
        if entry.error is not None:
            problems.append(Problem(entry.path, f"cannot parse ({entry.error})"))
            continue
        for name in sorted(entry.names):
            if name in config.external or name in config.unresolved:
                continue
            spec = config.modules.get(name)
            if spec is None:
                problems.append(Problem(entry.path, f"unmapped import {name!r}"))
                continue
            group = spec.group or chapter_group(entry.chapter)
            used[group].add(spec.dist)
            if spec.dist not in groups.get(group, set()):
                problems.append(
                    Problem(entry.path, f"{name!r} needs {spec.dist!r} in group {group!r}")
                )
    for group, declared in sorted(groups.items()):
        if group == "dev":
            continue
        unused = declared - used.get(group, set())
        unused -= config.declared_without_import.get(group, frozenset())
        problems.extend(
            Problem(f"pyproject.toml [{group}]", f"{dist!r} is declared but never imported")
            for dist in sorted(unused)
        )
    return problems


def unresolved_imports(results: Sequence[FileImports], config: Config) -> list[Problem]:
    """List every use of an import declared in ``[unresolved]``.

    These are known breaks that no installable dependency fixes yet. They are
    reported as warnings rather than failures so CI stays meaningful while the
    break remains visible in every run.

    Args:
        results: Output of :func:`scan`.
        config: Scanner configuration.

    Returns:
        One entry per file and unresolved import, in path order.
    """
    return [
        Problem(entry.path, f"imports {name!r}, which nothing installs: {config.unresolved[name]}")
        for entry in results
        for name in sorted(entry.names)
        if name in config.unresolved
    ]


def check_importable(
    results: Sequence[FileImports], config: Config, skip_groups: Iterable[str] = ()
) -> list[Problem]:
    """Import every third-party module that applies to the running interpreter.

    Only distributions from PyPI are imported; book code is never executed.

    Args:
        results: Output of :func:`scan`.
        config: Scanner configuration.
        skip_groups: Dependency groups that are not installed and must be skipped.

    Returns:
        One problem per module that failed to import.
    """
    skip = set(skip_groups)
    wanted: set[str] = set()
    for entry in results:
        for name in entry.names:
            spec = config.modules.get(name)
            if spec is None or not spec.applies_here():
                continue
            if (spec.group or chapter_group(entry.chapter)) not in skip:
                wanted.add(name)
    problems: list[Problem] = []
    for name in sorted(wanted):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - report any import-time failure
            problems.append(Problem(name, f"import failed: {type(exc).__name__}: {exc}"))
    return problems


def render_report(results: Sequence[FileImports], config: Config) -> str:
    """Render a Markdown table summarizing each chapter's requirements.

    Args:
        results: Output of :func:`scan`.
        config: Scanner configuration.

    Returns:
        Markdown text ending with a newline.
    """
    by_chapter: dict[str, set[str]] = defaultdict(set)
    chapters: set[str] = set()
    for entry in results:
        chapters.add(entry.chapter)
        by_chapter[entry.chapter].update(entry.names)

    lines = [
        "| Chapter | `uv` group | PyPI packages | Outside PyPI |",
        "| --- | --- | --- | --- |",
    ]
    for chapter in sorted(chapters):
        names = by_chapter[chapter]
        packages: dict[str, set[str]] = defaultdict(set)
        for name in names:
            if (spec := config.modules.get(name)) is not None:
                packages[spec.group or chapter_group(chapter)].add(_describe(spec))
        external = sorted({config.external[n] for n in names if n in config.external})
        external += sorted(
            f"**Unresolved:** {config.unresolved[n]}" for n in names if n in config.unresolved
        )
        group_cell = ", ".join(f"`{g}`" for g in sorted(packages)) or "-"
        package_cell = ", ".join(sorted(p for ps in packages.values() for p in ps)) or "-"
        lines.append(
            f"| {chapter} | {group_cell} | {package_cell} | {'; '.join(external) or '-'} |"
        )
    return "\n".join(lines) + "\n"


def _describe(spec: ModuleSpec) -> str:
    """Return a short human-readable label for a distribution and its limits."""
    limits: list[str] = []
    if spec.platform is not None:
        name = spec.platform.lstrip("!")
        label = _PLATFORM_NAMES.get(name, name)
        limits.append(f"not {label}" if spec.platform.startswith("!") else label)
    if spec.min_python is not None:
        limits.append(f"Python {spec.min_python[0]}.{spec.min_python[1]}+")
    if spec.max_python is not None:
        limits.append(f"Python <{spec.max_python[0]}.{spec.max_python[1]}")
    return f"`{spec.dist}`" + (f" ({', '.join(limits)})" if limits else "")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("report", help="print a Markdown table of chapter requirements")
    req_parser = sub.add_parser("requirements", help="generate pip requirements files")
    req_parser.add_argument(
        "--check", action="store_true", help="fail if the files are out of date"
    )
    check_parser = sub.add_parser("check", help="verify pyproject.toml matches the imports")
    check_parser.add_argument(
        "--import",
        dest="do_import",
        action="store_true",
        help="also import each third-party module available on this interpreter",
    )
    check_parser.add_argument(
        "--skip-group",
        action="append",
        default=[],
        metavar="GROUP",
        help="with --import, skip modules from a group that is not installed (repeatable)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface.

    Args:
        argv: Arguments to parse instead of ``sys.argv[1:]``.

    Returns:
        Process exit status: ``0`` on success, ``1`` if problems were found.
    """
    args = build_parser().parse_args(argv)
    root: Path = args.root.resolve()
    if args.command == "requirements":
        drift = sync_requirements(root, check_only=args.check)
        for problem in drift:
            print(problem, file=sys.stderr)
        return 1 if drift else 0

    config = Config.load(root / CONFIG_NAME)
    results = scan(root, config)

    if args.command == "report":
        sys.stdout.write(render_report(results, config))
        return 0

    for warning in unresolved_imports(results, config):
        print(f"WARNING: {warning}", file=sys.stderr)
    problems = check(results, config, load_groups(root / "pyproject.toml"))
    if args.do_import:
        problems += check_importable(results, config, args.skip_group)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print(f"OK: {len(results)} files consistent with pyproject.toml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
