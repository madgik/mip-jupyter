import os


def _env(name, default):
    return os.environ.get(name, default)


c.JupyterHub.spawner_class = "kubespawner.KubeSpawner"
c.KubeSpawner.image = _env("JUPYTER_SINGLEUSER_IMAGE", "hbpmip/mip-jupyter:dev")
c.KubeSpawner.namespace = _env("JUPYTERHUB_NAMESPACE", os.environ.get("POD_NAMESPACE", "default"))

# Pass platform backend URL to all spawned notebooks.
c.KubeSpawner.environment = {
    "PLATFORM_BACKEND_URL": _env("PLATFORM_BACKEND_URL", "http://platform-backend-service:8080/services"),
    "JUPYTER_TOKEN": _env("JUPYTER_SINGLEUSER_TOKEN", ""),
}

# Persistence configuration.
c.KubeSpawner.storage_class = _env("JUPYTER_STORAGE_CLASS", "k8s-local-storage")
c.KubeSpawner.storage_capacity = _env("JUPYTER_STORAGE_CAPACITY", "2Gi")

# Resource limits for spawned notebooks.
c.KubeSpawner.cpu_limit = float(_env("JUPYTER_CPU_LIMIT", "1"))
c.KubeSpawner.mem_limit = _env("JUPYTER_MEM_LIMIT", "1Gi")
c.KubeSpawner.cpu_guarantee = _env("JUPYTER_CPU_GUARANTEE", "500m")
c.KubeSpawner.mem_guarantee = _env("JUPYTER_MEM_GUARANTEE", "512Mi")

# Security: ensure pods run as the jovyan user.
c.KubeSpawner.pod_security_context = {
    "fsGroup": 100,
    "runAsUser": 1000,
}
