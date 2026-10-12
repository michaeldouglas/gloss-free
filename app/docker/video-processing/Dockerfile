# syntax=docker/dockerfile:1

FROM python:3.13.7-slim-bookworm@sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/workspace/app/.venv/bin:${PATH}"

WORKDIR /workspace/app

RUN apt-get update \
    && apt-get install --no-install-recommends --yes ca-certificates ffmpeg \
    && python -m pip install --no-cache-dir "uv==0.9.12" \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
COPY dataset ./dataset

RUN uv sync --frozen --no-dev

RUN groupadd --gid 10001 video \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin video \
    && mkdir -p /workspace/data/raw /workspace/data/processed /workspace/data/manifests \
    && chown -R video:video /workspace

USER video

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ffprobe -version >/dev/null 2>&1 && python --version >/dev/null 2>&1 || exit 1

# The default command is a lightweight toolchain check. Override it with
# ffprobe, ffmpeg, or a Python pipeline when running the service.
CMD ["ffprobe", "-version"]
