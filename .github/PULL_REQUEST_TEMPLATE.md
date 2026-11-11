## Summary

<!-- What does this change and why? Link the issue it resolves. -->

## Type

- [ ] Bug fix in book code
- [ ] Compatibility or dependency update
- [ ] Documentation
- [ ] Tooling, CI or packaging

## Checklist

- [ ] Behavioural changes to book code are recorded in `docs/CONVERSION_NOTES.md`
- [ ] User-visible changes are listed under `## [Unreleased]` in `CHANGELOG.md`
- [ ] If dependencies changed: `uv lock` and `python tools/deps_scan.py requirements` were run
- [ ] `uv run python tools/deps_scan.py check --import` passes locally
