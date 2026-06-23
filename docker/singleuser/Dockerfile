FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /usr/local/bin/

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLATFORM_BACKEND_URL=http://platform-backend:8080/services \
    JUPYTER_HOST=0.0.0.0 \
    JUPYTER_PORT=8888 \
    MIP_WORK_DIR=/home/jovyan/work \
    MIP_WORKSPACE_TEMPLATE=/opt/mip-workspace-template

RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 -s /bin/bash jovyan \
    && mkdir -p /home/jovyan/work

WORKDIR /opt/mip-build
COPY python-client/ ./python-client/
RUN uv pip install --system \
    "./python-client[notebook]" \
    "jupyterlab>=4.4,<4.6" \
    "ipykernel>=6,<8"

COPY workspace/ "${MIP_WORKSPACE_TEMPLATE}/"
COPY docker/singleuser/entrypoint.sh /usr/local/bin/mip-jupyter-entrypoint.sh
RUN chmod +x /usr/local/bin/mip-jupyter-entrypoint.sh \
    && chown -R jovyan:jovyan /home/jovyan "${MIP_WORKSPACE_TEMPLATE}"

WORKDIR /home/jovyan/work
USER jovyan

EXPOSE 8888
ENTRYPOINT ["tini", "--", "mip-jupyter-entrypoint.sh"]
