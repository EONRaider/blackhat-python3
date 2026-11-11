# Security policy

## What this repository is

This repository is offensive-security teaching material. It contains working
attack code from _Black Hat Python_ by Justin Seitz: scanners, sniffers, brute forcers
and, in places, malware-like tools. **That is intended, and it is not a vulnerability.**

Some files are flagged by antivirus or endpoint-protection software. Those
detections are expected. Exclude the folder from scanning on a lab machine, or use
the Docker image or dev container.

## Reporting a vulnerability

Report issues with the **project infrastructure** privately through
[GitHub private vulnerability reporting](https://github.com/EONRaider/blackhat-python3/security/advisories/new).
In scope:

- a dependency pinned in `pyproject.toml` / `uv.lock` with a known vulnerability
  that Dependabot has not picked up;
- a weakness in the GitHub Actions workflows, the Dockerfile or the dev container,
  such as script injection, excessive token permissions or an unpinned third-party
  action;
- a real secret committed by mistake. `chapter*/` sample keys and credentials are
  public test data and are documented in `NOTICE`.

Out of scope: "the code can be used to attack systems" and antivirus detections of
the book's tools.

Please allow a reasonable time for a fix before public disclosure.

## Supported versions

Only the latest release and the default branch receive fixes.
