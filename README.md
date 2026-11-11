# Black Hat Python 3

[![CI](https://github.com/EONRaider/blackhat-python3/actions/workflows/ci.yml/badge.svg)](https://github.com/EONRaider/blackhat-python3/actions/workflows/ci.yml)
[![Python 3.10-3.14](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Managed with uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://docs.astral.sh/uv/)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/EONRaider/blackhat-python3)

The source code from the first edition of **_Black Hat Python: Python Programming for
Hackers and Pentesters_** by Justin Seitz (No Starch Press, 2014), converted from
Python 2 to Python 3 and refactored to run on current interpreters and libraries.

The scripts stay close to the printed listings so they can be read side by side with
the book. Every change made during the conversion is documented in
[docs/CONVERSION_NOTES.md](docs/CONVERSION_NOTES.md).

> [!NOTE]
> No Starch Press published a
> [second edition](https://nostarch.com/black-hat-python2E) in 2021, by Justin Seitz
> and Tim Arnold, written for Python 3 from the start. This repository follows the
> **first** edition. If you have the second edition, use the publisher's code instead.
>
> A companion conversion of _Violent Python_ by TJ O'Connor lives at
> [EONRaider/violent-python3](https://github.com/EONRaider/violent-python3).

## Contents

- [Quick start](#quick-start)
- [Chapters](#chapters)
- [Downloading only what you need](#downloading-only-what-you-need)
- [Authorized use](#authorized-use)
- [Contributing](#contributing)
- [Translations](#translations)
- [License and credits](#license-and-credits)

## Quick start

Python 3.10 or newer. Pick one of the following setups.

### uv (recommended)

[uv](https://docs.astral.sh/uv/getting-started/installation/) installs the right
Python version if you don't have it and reproduces the exact dependency versions
tested in CI from `uv.lock`.

```shell
git clone https://github.com/EONRaider/blackhat-python3.git
cd blackhat-python3
uv sync                              # every chapter
uv run python chapter02/bhnet.py -h
```

Each chapter is a separate [dependency group](https://peps.python.org/pep-0735/), so you
can install only what you are reading:

```shell
uv sync --only-group ch04            # just chapter 4
```

On Windows, the `ch08`-`ch10` groups also install `pywin32` and `wmi`; on other
platforms they are skipped automatically.

### pip

```shell
git clone https://github.com/EONRaider/blackhat-python3.git
cd blackhat-python3
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt      # every chapter
pip install -r requirements/ch04.txt # or just one chapter
```

`requirements*.txt` carry version ranges. For the exact versions tested in CI, use
`requirements-lock.txt` from the [latest release](https://github.com/EONRaider/blackhat-python3/releases/latest).
With pip 25.1 or newer, you can also install a chapter's group straight from
`pyproject.toml` with `pip install --group ch04`.

### Docker

Each [release](https://github.com/EONRaider/blackhat-python3/releases) publishes an
image for `linux/amd64` and `linux/arm64` with every cross-platform chapter's
dependencies and common network tools preinstalled:

```shell
docker run --rm -it ghcr.io/eonraider/blackhat-python3
# Chapters that sniff or forge packets need raw-socket capabilities:
docker run --rm -it --cap-add=NET_RAW --cap-add=NET_ADMIN ghcr.io/eonraider/blackhat-python3
# Or build it yourself:
docker build -t blackhat-python3 . && docker run --rm -it blackhat-python3
```

The image runs as `root` because most raw-socket chapters need it. The container
is the sandbox, so only add the capabilities a chapter needs. The Windows chapters
(8-10) can't run in it.

### GitHub Codespaces / Dev Containers

Use the **Open in GitHub Codespaces** badge above, or open the folder in VS Code or
JetBrains with the Dev Containers extension. The container
([.devcontainer/devcontainer.json](.devcontainer/devcontainer.json)) has the same tools
as the Docker image, plus `uv`, `git` and compilers, and comes with raw-socket
capabilities already granted.

## Chapters

| Chapter | Topic | `uv` group | PyPI packages | Notes |
| --- | --- | --- | --- | --- |
| [02](chapter02) | The network: basics | `ch02` | `paramiko` | `test_rsa.key` is Paramiko's public test key (from its test suite), needed by `bh_sshserver.py`. |
| [03](chapter03) | Raw sockets and sniffing | - | - | Standard library only. Needs root / Administrator. |
| [04](chapter04) | Owning the network with Scapy | `ch04` | `kamene`, `opencv-python` | Uses `kamene`, a Python 3 fork of Scapy from the time of the conversion. Needs root / `NET_RAW`. |
| [05](chapter05) | Web hackery | - | - | Standard library only. Wordlists `all.txt` and `cain.txt` are included. |
| [06](chapter06) | Extending Burp Proxy | - | - | Burp Suite extensions that run under Jython 2.7 (`jython-standalone-2.7.2.jar` is included), not CPython. |
| [07](chapter07) | GitHub command and control | `ch07` | `github3.py` | Needs a GitHub repository and a personal access token. |
| [08](chapter08) | Common trojaning tasks on Windows | `ch08` | `pywin32` (Windows) | Windows only. `keylogger.py` does not run on Python 3.10+ yet: it imports `pyHook`, which nothing installable provides (see the conversion notes). |
| [09](chapter09) | Fun with Internet Explorer | `ch09` | `pycryptodome`, `pywin32` (Windows) | Windows only, except the crypto helpers. |
| [10](chapter10) | Windows privilege escalation | `ch10` | `pywin32` (Windows), `wmi` (Windows) | Windows only. `bhvulnservice.zip` is the book's vulnerable service. |
| [11](chapter11) | Automating offensive forensics | - | - | Needs Immunity Debugger (`immlib`, Python 2.7) and the Volatility 2 framework. Neither installs from PyPI. |

Chapter 1 of the book covers setting up the environment and has no code. The PyPI
column is generated by `python tools/deps_scan.py report`, which reads the imports in
each chapter. The OS and privilege notes come from the conversion notes and may be
incomplete; corrections are welcome.

## Downloading only what you need

A full checkout is about 46 MB plus 51 MB of history. Most of the tree is the 43 MB
Jython JAR in `chapter06/`, so shallow clones (`--depth 1`) don't save much. To
download just the chapters you want:

```shell
git clone --filter=blob:none --sparse https://github.com/EONRaider/blackhat-python3.git
cd blackhat-python3
git sparse-checkout set chapter02 chapter03    # any chapters you want
```

Or skip cloning entirely and use the [Docker image](#docker).

## Authorized use

This code includes trojans, keyloggers, credential harvesters and privilege-escalation
tooling. Run it only against systems you own or have written permission to test. Some
files, such as `chapter10/bhvulnservice.zip`, `chapter11/cmeasure.bin` and the
chapter 8 keylogger, may be flagged by antivirus software. That is expected; see
[SECURITY.md](SECURITY.md).

## Contributing

Bug fixes, compatibility fixes for newer libraries and documentation improvements are
welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the scope, the development
workflow and how releases are cut. Report security issues as described in
[SECURITY.md](SECURITY.md).

## Translations

- Turkish, by [Bedirhan Budak](https://github.com/bedirhanbudak): [`turkish-language` branch](https://github.com/EONRaider/blackhat-python3/tree/turkish-language)

## License and credits

The code is derived from _Black Hat Python_ by Justin Seitz, published by No Starch
Press. **No open-source license is granted**; see [NOTICE](NOTICE) for what that means
and for the terms of the bundled third-party files. The Python 3 conversion is by
[EONRaider](https://github.com/EONRaider) and
[contributors](https://github.com/EONRaider/blackhat-python3/graphs/contributors),
including fixes from Enraged.

If you reference this repository in academic work, GitHub's **Cite this repository**
button uses [CITATION.cff](CITATION.cff).
