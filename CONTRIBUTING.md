# Contributing

Thanks for helping keep this conversion of _Black Hat Python_ usable. This file
explains what kinds of change fit the project, how to set up a development
environment and how releases are made.

## What fits

This repository mirrors the book's listings so readers can follow along. Changes
that keep that goal are welcome:

- **Bug fixes** that make a listing work as the book describes.
- **Compatibility fixes** for newer Python versions or library releases.
- **Dependency updates**, including moving a capped dependency to its next major
  version once the affected chapter has been checked against it.
- **Documentation**: corrections to the README, `docs/CONVERSION_NOTES.md` or
  comments that explain how a listing differs from the printed book.

Changes that rewrite a listing beyond what the book shows (new features,
architectural refactors, style-only rewrites of book code) are better suited to a
fork. If you are unsure, open an issue first.

Record every behavioural change to book code in `docs/CONVERSION_NOTES.md`, so
readers comparing against the printed page know what differs and why.

## Development setup

You need [uv](https://docs.astral.sh/uv/getting-started/installation/). The dev
container in `.devcontainer/` provides everything else.

```shell
uv sync --all-groups          # every chapter, the opt-in extras and dev tools
uv run pre-commit install     # run the checks below before each commit
```

The opt-in groups are: none.

## Checks

CI runs all of these on every pull request. Run them locally first:

```shell
uv lock --check                                        # lockfile matches pyproject.toml
uv run python tools/deps_scan.py check --import        # imports match dependency groups
uv run python tools/deps_scan.py requirements --check  # requirements*.txt are current
uv run ruff format --check && uv run ruff check        # repository tooling only
uv run mypy && uv run pytest                           # repository tooling only
```

Ruff and mypy deliberately cover `tools/` only. Book code under `chapterNN/` keeps
the book's style and is not linted.

## Dependencies

Dependencies are declared per chapter as
[PEP 735 dependency groups](https://peps.python.org/pep-0735/) in `pyproject.toml`.
Groups: `ch02`, `ch04`, `ch07`, `ch08`, `ch09` and `ch10`. Chapters 3 and 5 use only the
standard library, chapter 6 runs under Jython inside Burp Suite, and chapter 11
needs tools that are not on PyPI.

To add or change one:

1. Edit the chapter's group in `pyproject.toml`. If the import name differs from
   the PyPI name (`cv2` and `opencv-python`, for example), add it to
   `tools/deps_scan.toml`.
2. Run `uv lock`.
3. Run `uv run python tools/deps_scan.py requirements` to regenerate
   `requirements.txt` and `requirements/*.txt`. Never edit those by hand.
4. Commit `pyproject.toml`, `uv.lock` and the regenerated files together.

Dependabot refreshes `uv.lock` weekly without touching the version ranges. Raising
a range past a major version is a deliberate change: check the affected chapter
first.

## Commits and pull requests

- Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
  (`fix(ch04): ...`, `build(deps): ...`, `docs: ...`).
- Keep each pull request to one topic and fill in the template.
- Add an entry under `## [Unreleased]` in `CHANGELOG.md` for user-visible changes.

## Releases

Maintainers only:

1. In `CHANGELOG.md`, rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD` and
   add a new empty `## [Unreleased]` above it.
2. Bump `version` in `pyproject.toml`, then run `uv lock`.
3. Merge to `master`, then tag and push: `git tag vX.Y.Z && git push origin vX.Y.Z`.

The `Release` workflow publishes the GitHub Release, with that changelog section
and a pinned `requirements-lock.txt`, and pushes the container image to
`ghcr.io/eonraider/blackhat-python3`.
