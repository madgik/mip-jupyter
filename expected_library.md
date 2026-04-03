# MIP Jupyter Expected Library (Init)

This document initializes the expected contract for the notebook-side library built in
`mip-jupyter` and consumed inside Jupyter/JupyterHub.

## System Context (Authoritative)

- Experiment execution engine: `exaflow/`
- API gateway to the engine: `platform-backend/` (`/services/...` endpoints)
- Web application: `platform-ui/`
- Notebook/client library home: `mip-jupyter/`
- Containerized integration test environment: `mip/deployment/dev/`

Design rule: notebook code must call `platform-backend`; it must not call Exaflow internals
directly. Exaflow remains an internal execution engine behind backend APIs.

## Library Goals

- Provide a clean, notebook-friendly API for metadata discovery and experiment execution.
- Keep backend transport details hidden behind a small client surface.
- Support authenticated and non-authenticated dev deployments (including JupyterHub mode).
- Return Python-native objects and sklearn-compatible models where relevant.

## Runtime Wiring

- Default backend base URL should resolve in both compose and local runs:
  - `http://platform-backend:8080/services`
  - fallbacks: `platform-backend-service`, `localhost`, `172.17.0.1`
- Token resolution order:
  - explicit `configure(token=...)`
  - `PLATFORM_TOKEN`, `PORTAL_TOKEN`
  - local token file (`mip_token` or `.mip_token`)
- In JupyterHub mode, token refresh may happen through the hub helper endpoint.

## Expected Public API (Notebook-Facing)

```python
from mip import (
    configure,
    metadata,
    algorithms,
    experiments,
    filters,
    FederatedLogisticRegression,
    FederatedLinearRegression,
    FederatedNaiveBayes,
)
```

### 1) Configuration

```python
configure(
    base_url="http://localhost:8080/services",
    token="<bearer-token>",
    timeout=30,
    allow_redirects=False,
)
```

### 2) Metadata Discovery

```python
models = metadata.list()                   # available data models/pathologies
p = metadata.get_pathology("dementia:0.1") # alias to selected data model
vars_ = p.variables
datasets = p.datasets

# tree view of metadata hierarchy (groups/subgroups/variables)
metadata.describe("dementia:0.1")
# include variable leaves
metadata.describe("dementia:0.1", include_variables=True)
```

### 3) Algorithm Discovery

```python
algos = algorithms.list()
```

### 4) Experiment Lifecycle

```python
from mip import experiments

exp = experiments.create(
    name="lr-demo",
    algorithm_name="logistic_regression",
    data_model="dementia:0.1",
    datasets=["edsd"],
    x=["lefthippocampus", "righthippocampus"],
    y=["alzheimerbroadcategory"],
    filters=None,
    parameters={"positive_class": "AD"},
)

exp.wait(timeout=120)
result = exp.results
```

### 5) Transient (Synchronous) Runs

```python
exp = experiments.run_transient(
    name="quick-run",
    algorithm_name="linear_regression",
    data_model="dementia:0.1",
    datasets=["edsd"],
    x=["age", "lefthippocampus"],
    y=["rightamygdala"],
)
```

### 6) sklearn-Compatible Wrappers

```python
result = FederatedLogisticRegression({
    "name": "lr-model",
    "data_model": "dementia:0.1",
    "datasets": ["edsd"],
    "x": ["lefthippocampus", "righthippocampus"],
    "y": ["alzheimerbroadcategory"],
    "parameters": {"positive_class": "AD"},
})

sk = result.get_sklearn_params()

from sklearn.linear_model import LogisticRegression
import numpy as np

model = LogisticRegression().set_params(**sk["set_params"])
fitted = sk["fitted_attributes"]
model.classes_ = np.asarray(fitted["classes_"])
model.coef_ = np.asarray(fitted["coef_"], dtype=float)
model.intercept_ = np.asarray(fitted["intercept_"], dtype=float)
model.n_features_in_ = int(fitted["n_features_in_"])
model.n_iter_ = np.asarray(fitted.get("n_iter_", [1]), dtype=np.int32)

pred = model.predict(df)
proba = model.predict_proba(df)
```

## Filters Contract

The library must expose a stable filter DSL for backend-compatible rulesets:

```python
from mip.filters import AND, OR, EQUAL, GREATER, RULESET

rule = ("age", GREATER, 60)
ruleset = RULESET([rule], AND)
```

Filters are serialized into the backend `algorithm.inputdata.filters` payload shape.

## Error Handling Expectations

- If backend redirects instead of returning JSON, raise a clear auth/base-url error.
- If token is expired, raise actionable guidance (or refresh via JupyterHub when available).
- For failed experiments, raise with `uuid`, status, and backend error details.

## Integration and Validation

Primary integration environment is `mip/deployment/dev/`.

Minimum validation for every library change:

1. Unit tests in `mip-jupyter/python-client/tests`.
2. Smoke run against `mip/deployment/dev` stack (backend + notebook mode when relevant).
3. Verify round-trip behavior for at least one algorithm call routed through:
   Jupyter library -> platform-backend -> Exaflow -> platform-backend response.

## Scope Boundary

- `mip-jupyter` owns notebook images + Python client library behavior.
- `platform-backend` owns API contracts and orchestration toward Exaflow.
- `exaflow` owns algorithm execution and federated engine internals.
- `platform-ui` is a separate consumer of backend APIs and not a dependency of notebook library code.
