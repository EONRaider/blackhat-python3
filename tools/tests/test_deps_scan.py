"""Tests for tools/deps_scan.py, run against a synthetic repository tree."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import deps_scan

CONFIG = """
[modules]
scapy = { dist = "scapy" }
PIL = { dist = "Pillow" }
crypt = { dist = "standard-crypt", platform = "!win32", min_python = "3.13" }
winonly = { dist = "pywin32", platform = "win32" }
bluetooth = { dist = "pybluez", group = "ch05-bt" }

[external]
burp = "Burp Suite"

[unresolved]
oldhook = "no installable package provides it"

[declared_without_import]
ch05 = ["extra-dist"]

[exclude]
files = ["chapter09/skip_me.py"]
"""

PYPROJECT = """
[dependency-groups]
ch01 = ["standard-crypt>=3.13; python_version >= '3.13'"]
ch02 = ["scapy>=2.6,<3", "pillow>=10"]
ch05 = ["extra-dist"]
ch05-bt = ["pybluez @ git+https://example.invalid/pybluez"]
dev = ["pytest"]

[tool.uv]
default-groups = ["ch01", "ch02", "ch05", "dev"]
"""


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    write(tmp_path, "tools/deps_scan.toml", CONFIG)
    write(tmp_path, "pyproject.toml", PYPROJECT)
    write(tmp_path, "chapter01/crack.py", "import crypt\nimport os\n")
    write(
        tmp_path,
        "chapter02/sniff.py",
        "from scapy.all import sniff\nfrom PIL import Image\nimport helper\nfrom . import rel\n",
    )
    write(tmp_path, "chapter02/helper.py", "x = 1\n")
    write(tmp_path, "chapter05/bt.py", "import bluetooth\n")
    write(tmp_path, "chapter06/ext.py", "from burp import IBurpExtender\n")
    write(tmp_path, "chapter08/hook.py", "import oldhook\n")
    write(tmp_path, "chapter09/skip_me.py", "import not_mapped\n")
    return tmp_path


def load(repo: Path) -> tuple[deps_scan.Config, list[deps_scan.FileImports]]:
    config = deps_scan.Config.load(repo / deps_scan.CONFIG_NAME)
    return config, deps_scan.scan(repo, config)


class TestHelpers:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("PyPDF4", "pypdf4"), ("github3.py", "github3-py"), ("Foo__Bar", "foo-bar")],
    )
    def test_normalize(self, raw: str, expected: str) -> None:
        assert deps_scan.normalize(raw) == expected

    def test_chapter_group(self) -> None:
        assert deps_scan.chapter_group("chapter4") == "ch04"
        assert deps_scan.chapter_group("chapter11") == "ch11"

    def test_chapter_group_rejects_other_dirs(self) -> None:
        with pytest.raises(ValueError, match="not a chapter directory"):
            deps_scan.chapter_group("tools")

    def test_extract_imports_ignores_relative_and_takes_top_level(self) -> None:
        source = "import a.b, c\nfrom d.e import f\nfrom . import g\nfrom .h import i\n"
        assert deps_scan.extract_imports(source) == {"a", "c", "d"}

    def test_extract_imports_tolerates_invalid_escapes(self) -> None:
        assert deps_scan.extract_imports('import re\nP = "\\d"\n') == {"re"}

    def test_extract_imports_raises_on_python2(self) -> None:
        with pytest.raises(SyntaxError):
            deps_scan.extract_imports('print "hello"\n')

    def test_load_groups_normalizes_names(self, repo: Path) -> None:
        groups = deps_scan.load_groups(repo / "pyproject.toml")
        assert groups["ch02"] == {"scapy", "pillow"}
        assert groups["ch05-bt"] == {"pybluez"}

    def test_config_rejects_entry_without_dist(self, tmp_path: Path) -> None:
        write(tmp_path, "c.toml", "[modules]\nfoo = { platform = 'linux' }\n")
        with pytest.raises(ValueError, match="must be a table with a 'dist' key"):
            deps_scan.Config.load(tmp_path / "c.toml")


class TestModuleSpec:
    def test_platform_gate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "platform", "linux")
        assert not deps_scan.ModuleSpec("pywin32", platform="win32").applies_here()
        assert deps_scan.ModuleSpec("x", platform="linux").applies_here()

    def test_negated_platform_gate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        spec = deps_scan.ModuleSpec("standard-crypt", platform="!win32")
        monkeypatch.setattr(sys, "platform", "win32")
        assert not spec.applies_here()
        monkeypatch.setattr(sys, "platform", "darwin")
        assert spec.applies_here()

    def test_python_gate(self) -> None:
        future = (sys.version_info.major, sys.version_info.minor + 1)
        assert not deps_scan.ModuleSpec("x", min_python=future).applies_here()
        assert deps_scan.ModuleSpec("x", min_python=(3, 0)).applies_here()


class TestScan:
    def test_filters_stdlib_and_local_but_keeps_mapped(self, repo: Path) -> None:
        _, results = load(repo)
        by_path = {r.path: r.names for r in results}
        assert by_path["chapter01/crack.py"] == {"crypt"}
        assert by_path["chapter02/sniff.py"] == {"scapy", "PIL"}
        assert "chapter09/skip_me.py" not in by_path

    def test_records_parse_errors(self, repo: Path) -> None:
        write(repo, "chapter03/py2.py", 'print "x"\n')
        _, results = load(repo)
        (entry,) = [r for r in results if r.path == "chapter03/py2.py"]
        assert entry.error is not None
        assert entry.error.startswith("line 1")


class TestCheck:
    def test_consistent_repo_passes(self, repo: Path) -> None:
        config, results = load(repo)
        groups = deps_scan.load_groups(repo / "pyproject.toml")
        assert deps_scan.check(results, config, groups) == []

    def test_reports_missing_unmapped_unused_and_unparseable(self, repo: Path) -> None:
        write(repo, "chapter02/more.py", "import requests\nimport winonly\n")
        write(repo, "chapter03/py2.py", 'print "x"\n')
        write(repo, "pyproject.toml", PYPROJECT.replace('"pillow>=10"', '"pillow>=10", "lxml"'))
        config, results = load(repo)
        groups = deps_scan.load_groups(repo / "pyproject.toml")
        messages = {str(p) for p in deps_scan.check(results, config, groups)}
        assert messages == {
            "chapter02/more.py: unmapped import 'requests'",
            "chapter02/more.py: 'winonly' needs 'pywin32' in group 'ch02'",
            "chapter03/py2.py: cannot parse (line 1: Missing parentheses in call to 'print'."
            " Did you mean print(...)?)",
            "pyproject.toml [ch02]: 'lxml' is declared but never imported",
        }

    def test_check_importable_reports_failures(self, repo: Path) -> None:
        config = deps_scan.Config(
            modules={
                "json": deps_scan.ModuleSpec("json"),
                "definitely_missing_mod": deps_scan.ModuleSpec("missing"),
                "skipped_mod": deps_scan.ModuleSpec("x", platform="no-such-platform"),
            },
            external={},
            exclude=frozenset(),
        )
        results = [
            deps_scan.FileImports(
                "chapter01/a.py",
                "chapter01",
                {"json", "definitely_missing_mod", "skipped_mod"},
            )
        ]
        problems = deps_scan.check_importable(results, config)
        assert [p.location for p in problems] == ["definitely_missing_mod"]
        assert "ModuleNotFoundError" in problems[0].message

    def test_check_importable_skips_groups(self, repo: Path) -> None:
        config, results = load(repo)
        problems = deps_scan.check_importable(results, config, skip_groups={"ch05-bt", "ch02"})
        assert all(p.location not in {"bluetooth", "scapy", "PIL"} for p in problems)


class TestReportAndCli:
    def test_report_table(self, repo: Path) -> None:
        config, results = load(repo)
        report = deps_scan.render_report(results, config)
        assert "| chapter02 | `ch02` | `pillow`, `scapy` | - |" in report
        assert "| chapter05 | `ch05-bt` | `pybluez` | - |" in report
        assert "| chapter06 | - | - | Burp Suite |" in report
        assert (
            "| chapter08 | - | - | **Unresolved:** no installable package provides it |" in report
        )
        assert "`standard-crypt` (not Windows, Python 3.13+)" in report

    def test_main_report(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert deps_scan.main(["--root", str(repo), "report"]) == 0
        assert capsys.readouterr().out.startswith("| Chapter |")

    def test_main_check_ok(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert deps_scan.main(["--root", str(repo), "check"]) == 0
        assert capsys.readouterr().out.startswith("OK: 6 files")

    def test_main_check_fails(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        write(repo, "chapter02/more.py", "import requests\n")
        assert deps_scan.main(["--root", str(repo), "check"]) == 1
        assert "unmapped import 'requests'" in capsys.readouterr().err

    def test_main_check_import(self, repo: Path) -> None:
        write(repo, "tools/deps_scan.toml", "[external]\nburp = 'Burp'\n")
        write(repo, "pyproject.toml", "[dependency-groups]\n")
        for rel in (
            "chapter01/crack.py",
            "chapter02/sniff.py",
            "chapter05/bt.py",
            "chapter08/hook.py",
        ):
            (repo / rel).unlink()
        (repo / "chapter09/skip_me.py").unlink()
        assert deps_scan.main(["--root", str(repo), "check", "--import"]) == 0

    def test_main_check_import_with_skip(self, repo: Path) -> None:
        argv = ["--root", str(repo), "check", "--import", "--skip-group", "ch05-bt"]
        argv += ["--skip-group", "ch02", "--skip-group", "ch01"]
        assert deps_scan.main(argv) == 0


class TestRequirements:
    def test_render_dedupes_and_keeps_order(self) -> None:
        groups = {"a": ["x>=1", "y"], "b": ["y", "z; sys_platform == 'win32'"]}
        text = deps_scan.render_requirements(groups, ["a", "b"])
        lines = text.splitlines()
        assert lines[0].startswith("# Generated from pyproject.toml")
        assert lines[1].endswith("Groups: a, b")
        assert lines[2:] == ["x>=1", "y", "z; sys_platform == 'win32'"]

    def test_files_cover_defaults_and_each_group(self, repo: Path) -> None:
        files = deps_scan.requirements_files(repo / "pyproject.toml")
        assert set(files) == {
            "requirements.txt",
            "requirements/ch01.txt",
            "requirements/ch02.txt",
            "requirements/ch05.txt",
            "requirements/ch05-bt.txt",
        }
        assert "pybluez" not in files["requirements.txt"]
        assert "scapy>=2.6,<3" in files["requirements.txt"]
        assert "pytest" not in files["requirements.txt"]

    def test_write_then_check_roundtrip(self, repo: Path) -> None:
        write(repo, "requirements/old.txt", "stale\n")
        assert deps_scan.main(["--root", str(repo), "requirements", "--check"]) == 1
        assert deps_scan.main(["--root", str(repo), "requirements"]) == 0
        assert not (repo / "requirements/old.txt").exists()
        assert deps_scan.main(["--root", str(repo), "requirements", "--check"]) == 0

    def test_check_reports_each_problem(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        deps_scan.main(["--root", str(repo), "requirements"])
        write(repo, "requirements/ch02.txt", "edited\n")
        write(repo, "requirements/gone.txt", "x\n")
        assert deps_scan.main(["--root", str(repo), "requirements", "--check"]) == 1
        err = capsys.readouterr().err
        assert "requirements/ch02.txt: out of date" in err
        assert "requirements/gone.txt: stale file" in err


class TestUnresolved:
    def test_unresolved_is_not_a_check_failure(self, repo: Path) -> None:
        config, results = load(repo)
        groups = deps_scan.load_groups(repo / "pyproject.toml")
        assert deps_scan.check(results, config, groups) == []

    def test_unresolved_imports_are_listed(self, repo: Path) -> None:
        config, results = load(repo)
        (warning,) = deps_scan.unresolved_imports(results, config)
        assert str(warning) == (
            "chapter08/hook.py: imports 'oldhook', which nothing installs: "
            "no installable package provides it"
        )

    def test_main_check_prints_warning(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert deps_scan.main(["--root", str(repo), "check"]) == 0
        err = capsys.readouterr().err
        assert "WARNING: chapter08/hook.py: imports 'oldhook'" in err
