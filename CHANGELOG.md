# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Releases are tagged
`vX.Y.Z`.

## [Unreleased]

## [2.0.0] - Unreleased

Modernizes the repository scaffolding: packaging, environments, CI and
documentation. **No book code under `chapterNN/` was changed.**

### Added

- `pyproject.toml` with one [PEP 735](https://peps.python.org/pep-0735/) dependency
  group per chapter, managed with [uv](https://docs.astral.sh/uv/), plus a committed
  `uv.lock`. Supports Python 3.11 to 3.14. Windows-only packages (`pywin32`,
  `wmi`, `pywinhook`) carry platform markers, so other systems skip them.
- `requirements/chNN.txt` for installing a single chapter with pip.
- Dockerfile and a multi-arch image (`ghcr.io/eonraider/blackhat-python3`). Images
  ship with SBOM and provenance attestations.
- Dev container configuration for GitHub Codespaces and local IDEs.
- `tools/deps_scan.py`: statically checks that every chapter's imports are declared
  in its dependency group, imports each dependency in CI, and generates the
  requirements files.
- GitHub Actions: an install matrix (Linux, macOS, Windows x Python 3.11-3.14), a
  Docker build, link checking, Markdown lint, actionlint and zizmor. Every action is
  pinned to a commit SHA.
- Dependabot for uv, GitHub Actions, Docker and dev containers.
- `NOTICE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1),
  `SECURITY.md`, `CITATION.cff`, issue forms and a pull request template.

### Changed

- The README was rewritten with setup instructions for uv, pip, Docker and
  Codespaces, a chapter table, and a pointer to the book's second edition. The
  conversion notes moved, otherwise unchanged, to `docs/CONVERSION_NOTES.md`.
- `requirements.txt` is now generated from `pyproject.toml`
  (`python tools/deps_scan.py requirements`). It lists version ranges, and each
  release attaches a pinned `requirements-lock.txt`.
- Python 3.10 and older are no longer supported. 3.10 reached end of life in
  October 2026, and current security releases of some dependencies (Pillow 13,
  for example) require 3.11.

### Possibly breaking: dependency major versions

The 2020 pins don't install on current Python. Ranges were raised to the oldest
releases that do, and these crossed a major version or a large API boundary. Each
installs and imports cleanly in CI on every supported Python, but runtime
behaviour against the book code has not been verified yet:

| Package | Was | Now | Used by |
| --- | --- | --- | --- |
| `paramiko` | `~=2.7.1` | `>=3.5.0,<4` | chapter02 |
| `github3.py` | `~=1.3.0` | `>=4.0.1,<5` | chapter07 |
| `opencv-python` | `~=4.5.1.48` | `>=4.10.0.84,<5` | chapter04 |

### Fixed

- `crypto~=1.4.1` was replaced with `pycryptodome`. The `crypto` package on PyPI is
  an unrelated command-line tool; chapter 9 imports `Crypto.*`, which
  `pycryptodome` provides.

### Removed

- Explicit pins of Paramiko's transitive dependencies (`bcrypt`, `cffi`,
  `cryptography`, `pycparser`, `PyNaCl`, `six`), now resolved by the lockfile. Their
  2020 versions did not build on Python 3.12+.

### Security

- Version floors no longer admit releases with known advisories:
  `pytest>=9.0.3` (dev). The lockfile moves `filelock`, a dependency of the
  `pre-commit` tooling, to 4.2.10.
- **Known issue:** `paramiko` 3.x, used by chapter 2, is affected by
  [CVE-2026-44405](https://github.com/advisories/GHSA-r374-rxx8-8654) (RSA keys
  accept SHA-1 signatures). The fix exists only in paramiko 5, which removes
  SHA-1 support, raises the minimum RSA modulus and reorganizes the key classes.
  The `<4` cap stays until chapter 2 has been verified against it.

## Before 2.0.0

The Python 3 conversion itself (2020) and later fixes are recorded in the git
history.

[Unreleased]: https://github.com/EONRaider/blackhat-python3/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/EONRaider/blackhat-python3/releases/tag/v2.0.0
