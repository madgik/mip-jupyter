# AGENTS.md

This file is the first stop for AI coding agents working in this repository. It is intentionally more direct than a human README: follow the API contract, keep notebook work reproducible, and avoid inventing platform behavior.

For the longer playbook, read [`docs/llm_agent_wiki.md`](docs/llm_agent_wiki.md).

## Mission

`mip-jupyter` provides:

1. Jupyter and JupyterHub image assets.
2. The notebook-facing `mip` Python client for federated analysis through `platform-backend`.
3. Example notebooks that show how analysts should explore metadata, build an `AnalysisSet`, define a `Pipeline`, and run backend-approved aggregate algorithms.

The Python client is a thin client over `platform-backend`. Notebook code must not call Exaflow directly.

## Repository map

- `README.md` - human setup guide and quick start.
- `expected_library.md` - public `mip` API contract. Treat this as the source of truth for agent-generated notebook code.
- `Welcome.ipynb` - runnable companion notebook for the MVP API.
- `feres_analysis.ipynb` - Feres stroke territory example notebook.
- `python-client/mip/` - notebook-facing client package.
- `python-client/tests/` - mocked unit tests. Tests must not require a live backend.
- `Dockerfile.jupyter` - single-user Jupyter image.
- `Dockerfile.jupyterhub` - JupyterHub image.
- `docs/llm_agent_wiki.md` - deeper onboarding and task playbook for LLM agents.

Do not hand-edit generated artifacts in `build/`, `*.egg-info/`, `__pycache__/`, or `.venv/`.

## Non-negotiable rules for agents

- Use only the public API that exists in this repo.
- Do not invent data model codes, dataset codes, variable codes, algorithm names, or result fields.
- Do not use `.table()`; no such public API exists.
- Do not use `Pipeline.run(...)` as the primary API.
- Do not create custom `VariableSet`, `VariableList`, `DatasetSet`, or `DatasetList` abstractions.
- Do not access patient-level data. Notebook outputs must come from backend-approved aggregate results.
- Do not call Exaflow directly from notebooks. Use the `mip` client through `platform-backend`.
- Do not commit real tokens or credentials.
- Do not make tests depend on live services. Mock HTTP in tests.

## Confirmed public API pattern

Use this style in notebooks:

```python
import mip
from mip.filters import F
from mip.preprocessing import (
    CategoricalColumnCreator,
    MissingValuesHandler,
    OutlierWinsorizer,
)

client = mip.Client.from_env()
catalog = client.catalog()
algorithms = client.algorithms()
```

Catalog discovery:

```python
catalog.list()
catalog.summaries()
catalog.tree()

dm = catalog.data_model("data_model_code")
dm.summary()
dm.datasets.list()
dm.datasets.search("search term")
dm.variables.list()
dm.variables.search("search term")
dm.tree(include_variables=True)
dm.variables.tree(group="group_code")
```

Analysis set:

```python
dataset = dm.datasets["dataset_code"]
variable = dm.variables["variable_code"]

analysis_set = mip.AnalysisSet(
    data_model=dm,
    datasets=[dataset],
    variables=[variable],
)

analysis_set.summary()
analysis_set.explain()
analysis_set.histogram(variable=variable, bins=20)
```

Pipeline:

```python
missing = MissingValuesHandler(strategies={variable: "median"})
outliers = OutlierWinsorizer(
    strategies={variable: "iqr"},
    tails={variable: "both"},
    folds={variable: 1.5},
)

pipeline = mip.Pipeline(
    analysis_set=analysis_set,
    filters=F(variable).is_not_null(),
    handle_missing=missing,
    outlier_handling=outliers,
)

pipeline.describe()
pipeline.histogram(variable=variable, bins=20)
```

Supported pipeline algorithm methods currently include:

```python
pipeline.describe()
pipeline.histogram(variable=variable, bins=20)
pipeline.t_test(variable=y, group_by=group, group_a="A", group_b="B")
pipeline.pearson_correlation(x=x, y=y)
pipeline.chi_square_test(x=x, y=y)
pipeline.logistic_regression(x=[x1, x2], y=y, positive_class="case")
```

Use `client.algorithms()` to inspect available backend algorithm metadata before assuming optional behavior.

## Notebook workflow for agents

When creating or editing analysis notebooks, work in this order:

1. Setup and imports.
2. Catalog exploration.
3. Data model selection from actual catalog output.
4. Dataset exploration and selection.
5. Variable search and metadata inspection.
6. Research question formulation based on available variables.
7. `AnalysisSet` creation.
8. Initial aggregate EDA.
9. Pipeline definition with filters/preprocessing.
10. Derived columns only when clinically/statistically useful.
11. Descriptive statistics after preprocessing.
12. Statistical significance tests.
13. Modeling only when justified.
14. Interpretation, limitations, and reproducibility summary.

Prefer Markdown before code cells. The notebook should read as an analysis report, not only a script.

## Preprocessing guidance

Use the provided builders:

```python
MissingValuesHandler(strategies={age: "median"})
OutlierWinsorizer(strategies={score: "iqr"}, tails={score: "both"}, folds={score: 1.5})
```

For derived categorical columns:

```python
creator = CategoricalColumnCreator(
    code="derived_group",
    rules={
        "high": F(score) >= 10,
        "low": F(score) < 10,
    },
    default_enumeration="unclassified",
)
derived_group = creator.variable
```

Document derived enumerations and use the returned `DerivedVariable` downstream when appropriate. If a source variable is used only to create a derived variable, avoid also using the source in the same final model unless clearly justified.

## Logistic regression and sklearn export

Use logistic regression only for a valid binary outcome:

```python
logreg = pipeline.logistic_regression(
    x=[age, sex, severity],
    y=outcome,
    positive_class="positive_label",
)
```

If sklearn export is available, inspect schema before export:

```python
schema = logreg.feature_schema()
sklearn_model = logreg.to_sklearn()
```

Local prediction requires local data already preprocessed by the user. Do not implement automatic local preprocessing. Local columns must match `sklearn_model.feature_names_in_`.

## Build and test commands

From the repository root:

```bash
uv sync
uv run mip-notebook
uv run python -m unittest discover -s python-client/tests -p "test_*.py"
uv run python python-client/verify_script.py
```

Without `uv`:

```bash
python3 -m pip install -e ./python-client
cd python-client && python3 -m unittest discover -s tests -p "test_*.py"
python3 python-client/verify_script.py
```

Docker builds:

```bash
docker build \
  --build-arg JUPYTER_SCIPY_IMAGE=jupyter/scipy-notebook@sha256:<digest> \
  -f Dockerfile.jupyter -t mip-jupyter:dev .

docker build -f Dockerfile.jupyterhub -t mip-jupyterhub:dev .
```

Pin the Jupyter base image digest for reproducible builds.

## Coding style

- Python 3, PEP 8 defaults, 4-space indentation.
- Modules/functions/variables: `snake_case`.
- Classes: `PascalCase`.
- Environment variables: `UPPER_SNAKE_CASE`.
- Keep error messages explicit.
- Keep tests deterministic and mocked.

## PR checklist for agents

Before opening or finishing a change, verify:

- Public API examples match `expected_library.md`.
- No `.table()` calls were added.
- No `Pipeline.run(...)` calls were added.
- No patient-level data access is attempted.
- Notebook cells are executable top-to-bottom.
- New client behavior has tests.
- Tests do not make live HTTP calls.
- No credentials, tokens, or private backend URLs are committed.
