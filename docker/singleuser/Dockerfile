# syntax=docker/dockerfile:1.7

FROM python:3.12-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

WORKDIR /opt/mip-build
COPY pyproject.toml uv.lock ./
COPY python-client/pyproject.toml python-client/README.md ./python-client/
COPY python-client/mip ./python-client/mip
COPY mip_jupyter_dev ./mip_jupyter_dev

# uv.sources marks mip editable for local dev; sync --no-editable copies wheels into the venv.
# uv venvs have no pip; add it so notebook `%pip install` works.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev \
    && uv pip install --python /opt/venv/bin/python pip

FROM node:20-bookworm-slim AS node-tools
RUN npm install -g --omit=dev @openai/codex @zed-industries/codex-acp \
    && npm cache clean --force \
    && rm -rf /root/.npm \
        /usr/local/include \
        /usr/local/share \
        /usr/local/lib/node_modules/npm \
        /usr/local/lib/node_modules/corepack \
        /usr/local/bin/npm \
        /usr/local/bin/npx \
        /usr/local/bin/corepack \
        /usr/local/bin/yarn \
        /usr/local/bin/pnpm

FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PLATFORM_BACKEND_URL=http://platform-backend:8080/services \
    JUPYTER_HOST=0.0.0.0 \
    JUPYTER_PORT=8888 \
    MIP_WORK_DIR=/home/jovyan/work \
    MIP_WORKSPACE_TEMPLATE=/opt/mip-workspace-template \
    MIP_JUPYTER_ROOT=/home/jovyan/work \
    MIP_AGENT_DOCS=/opt/mip-agent-docs \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

# gid 100 (users) matches KubeSpawner fsGroup.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 -g 100 -s /bin/bash jovyan \
    && mkdir -p /home/jovyan/work /etc/profile.d \
    && printf '%s\n' 'export PATH="/opt/venv/bin:$PATH"' > /etc/profile.d/mip-venv.sh \
    && chown -R 1000:100 /home/jovyan

COPY --from=node-tools /usr/local /usr/local
COPY --from=build --chown=1000:100 /opt/venv /opt/venv

COPY --chown=1000:100 workspace/ "${MIP_WORKSPACE_TEMPLATE}/"
COPY --chown=1000:100 docs/user/ "${MIP_WORKSPACE_TEMPLATE}/docs/"
COPY --chown=1000:100 docs/llm/ /opt/mip-agent-docs/llm/
COPY --chown=1000:100 AGENTS.md /opt/mip-agent-docs/
COPY --chmod=755 docker/singleuser/entrypoint.sh /usr/local/bin/mip-jupyter-entrypoint.sh

WORKDIR /home/jovyan/work
USER jovyan

EXPOSE 8888
ENTRYPOINT ["tini", "--", "mip-jupyter-entrypoint.sh"]
