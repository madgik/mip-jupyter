FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /uvx /usr/local/bin/

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLATFORM_BACKEND_URL=http://platform-backend:8080/services \
    JUPYTER_HOST=0.0.0.0 \
    JUPYTER_PORT=8888 \
    MIP_WORK_DIR=/home/jovyan/work \
    MIP_WORKSPACE_TEMPLATE=/opt/mip-workspace-template \
    MIP_JUPYTER_ROOT=/home/jovyan/work

RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 -s /bin/bash jovyan \
    && mkdir -p /home/jovyan/work

WORKDIR /opt/mip-build
COPY python-client/ ./python-client/
COPY pyproject.toml ./
COPY mip_jupyter_dev/ ./mip_jupyter_dev/
RUN uv pip install --system \
    "./python-client[notebook]" \
    "jupyterlab>=4.4,<4.6" \
    "jupyter-ai>=3,<4" \
    "notebook>=7.0.0,<8.0.0" \
    "nbconvert>=7.0.0,<8.0.0" \
    "ipykernel>=6,<8" \
    && uv pip install --system --no-deps .

COPY workspace/ "${MIP_WORKSPACE_TEMPLATE}/"
COPY docker/singleuser/entrypoint.sh /usr/local/bin/mip-jupyter-entrypoint.sh
RUN chmod +x /usr/local/bin/mip-jupyter-entrypoint.sh \
    && chown -R jovyan:jovyan /home/jovyan "${MIP_WORKSPACE_TEMPLATE}"

WORKDIR /home/jovyan/work
USER jovyan

EXPOSE 8888
ENTRYPOINT ["tini", "--", "mip-jupyter-entrypoint.sh"]
