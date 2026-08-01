# syntax=docker/dockerfile:1.7

FROM python:3.12-slim-bookworm AS build

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /usr/local/bin/

WORKDIR /opt/mip-build
COPY python-client/ ./python-client/
COPY pyproject.toml ./
COPY mip_jupyter_dev/ ./mip_jupyter_dev/

RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && uv pip install .


FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /usr/local/bin/

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLATFORM_BACKEND_URL=http://platform-backend:8080/services \
    JUPYTER_HOST=0.0.0.0 \
    JUPYTER_PORT=8888 \
    MIP_WORK_DIR=/home/jovyan/work \
    MIP_WORKSPACE_TEMPLATE=/opt/mip-workspace-template \
    MIP_JUPYTER_ROOT=/home/jovyan/work \
    MIP_AGENT_DOCS=/opt/mip-agent-docs \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends tini curl ca-certificates gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @openai/codex @zed-industries/codex-acp \
    && rm -rf /var/lib/apt/lists/* /root/.npm \
    && useradd -m -u 1000 -s /bin/bash jovyan \
    && mkdir -p /home/jovyan/work

COPY --from=build /opt/venv /opt/venv

COPY workspace/ "${MIP_WORKSPACE_TEMPLATE}/"
COPY docs/user/ "${MIP_WORKSPACE_TEMPLATE}/docs/"
COPY docs/llm/ /opt/mip-agent-docs/llm/
COPY AGENTS.md /opt/mip-agent-docs/
COPY docker/singleuser/entrypoint.sh /usr/local/bin/mip-jupyter-entrypoint.sh
RUN chmod +x /usr/local/bin/mip-jupyter-entrypoint.sh \
    && chown -R jovyan:jovyan /home/jovyan "${MIP_WORKSPACE_TEMPLATE}" /opt/mip-agent-docs /opt/venv

WORKDIR /home/jovyan/work
USER jovyan

EXPOSE 8888
ENTRYPOINT ["tini", "--", "mip-jupyter-entrypoint.sh"]
