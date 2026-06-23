#!/bin/sh
set -eu

WORK="${MIP_WORK_DIR:-/home/jovyan/work}"
TEMPLATE="${MIP_WORKSPACE_TEMPLATE:-/opt/mip-workspace-template}"

mkdir -p "${WORK}/scratch"

if [ ! -f "${WORK}/Welcome.ipynb" ]; then
  cp -a "${TEMPLATE}/." "${WORK}/"
fi

mkdir -p "${WORK}/scratch"

default_notebook="${MIP_NOTEBOOK:-Welcome.ipynb}"

exec jupyter lab \
  --no-browser \
  --ServerApp.ip="${JUPYTER_HOST:-0.0.0.0}" \
  --ServerApp.port="${JUPYTER_PORT:-8888}" \
  --ServerApp.token="${JUPYTER_TOKEN:-}" \
  --ServerApp.root_dir="${WORK}" \
  --ServerApp.default_url="/lab/tree/${default_notebook}"
