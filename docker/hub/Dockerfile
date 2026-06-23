FROM jupyterhub/jupyterhub:latest

RUN python3 -m pip install --no-cache-dir jupyterhub-kubespawner

COPY docker/hub/jupyterhub_config.py /etc/jupyterhub/jupyterhub_config.py

EXPOSE 8000
