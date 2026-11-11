# syntax=docker/dockerfile:1.7
#
# Container image for blackhat-python3: a ready-to-run environment with every
# chapter's Python dependencies and the system tools the book uses.
#
#   docker run --rm -it --cap-add=NET_RAW --cap-add=NET_ADMIN ghcr.io/eonraider/blackhat-python3
#
# The image runs as root on purpose: most chapters open raw sockets, which a
# non-root process cannot do even when the container holds CAP_NET_RAW. The
# container is the sandbox; grant capabilities only when a chapter needs them.

ARG PYTHON_VERSION=3.13
ARG UV_VERSION=0.13.7

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# ---------------------------------------------------------------------------
# builder: resolve and install the locked dependencies into /opt/venv
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential git \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ---------------------------------------------------------------------------
# base: system tools the chapters shell out to, plus the locked venv
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS base
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libpcap0.8 tcpdump iproute2 iputils-ping net-tools openssh-client netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH \
    VIRTUAL_ENV=/opt/venv \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---------------------------------------------------------------------------
# dev: base plus uv, git and build tools; used by .devcontainer/
# ---------------------------------------------------------------------------
FROM base AS dev
COPY --from=uv /uv /uvx /usr/local/bin/
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential git \
 && rm -rf /var/lib/apt/lists/*
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# ---------------------------------------------------------------------------
# runtime (default target): base plus the book code
# ---------------------------------------------------------------------------
FROM base AS runtime
LABEL org.opencontainers.image.title="blackhat-python3" \
      org.opencontainers.image.description="Python 3 source code for the book Black Hat Python" \
      org.opencontainers.image.source="https://github.com/EONRaider/blackhat-python3"
WORKDIR /opt/blackhat-python3
COPY . .
CMD ["bash"]
