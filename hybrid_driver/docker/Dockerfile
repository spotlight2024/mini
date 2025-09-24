# SpotLight Hybrid Driver API container managed purely by Poetry
FROM python:3.10-slim AS base

ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    API_HOST=0.0.0.0 \
    API_PORT=10001 \
    PIP_TIMEOUT=300 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    make \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# ---------------------------------------------------------------------------
# Build stage: install Poetry dependencies directly into the system site-packages
# ---------------------------------------------------------------------------
FROM base AS builder

ENV POETRY_VERSION=2.2.1 \
    POETRY_HOME=/opt/poetry \
    PATH="/opt/poetry/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry config installer.parallel true && \
    poetry install --only main --no-root --no-interaction --no-ansi

# ---------------------------------------------------------------------------
# Final image: copy installed dependencies and application code
# ---------------------------------------------------------------------------
FROM base AS runtime

WORKDIR /app

COPY --from=builder /usr/local /usr/local
COPY pyproject.toml poetry.lock ./
COPY hybrid_driver/ ./hybrid_driver/

RUN useradd -m -u 1000 spotlight && \
    mkdir -p logs data cache && \
    chown -R spotlight:spotlight /app

USER spotlight

EXPOSE 10001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10001/health || exit 1

CMD ["python", "hybrid_driver/start_api_server.py", "--host", "0.0.0.0", "--port", "10001"]
