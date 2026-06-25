FROM jupyterhub/jupyterhub:latest

RUN python3 -m pip install --no-cache-dir jupyterhub-kubespawner oauthenticator requests

COPY docker/hub/jupyterhub_config.py /etc/jupyterhub/jupyterhub_config.py
COPY docker/hub/platform_token_service.py /etc/jupyterhub/platform_token_service.py
COPY docker/hub/platform_token_utils.py /etc/jupyterhub/platform_token_utils.py

ENV PYTHONPATH=/etc/jupyterhub
ENV JUPYTERHUB_CONFIG=/etc/jupyterhub/jupyterhub_config.py

EXPOSE 8000
CMD ["jupyterhub", "-f", "/etc/jupyterhub/jupyterhub_config.py"]
