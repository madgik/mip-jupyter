# MIP Jupyter Expected Library

Contract for the notebook-side `mip` library built in `mip-jupyter` and consumed inside Jupyter/JupyterHub.

## System Context

- Experiment execution engine: `exaflow/`
- API gateway: `platform-backend/` (`/services/...`)
- Web application: `platform-ui/`
- Notebook client: `mip-jupyter/`

Design rule: notebook code calls `platform-backend` only, not Exaflow directly.

## Library Goals

- Discover data models and datasets before analysis (`catalog`)
- Express analysis state in an immutable `Context`
- Run federated statistics and models through `Analysis` namespaces
- Hide HTTP transport behind `configure()` and internal `PortalClient`
- Return notebook-friendly `ResultTable` objects with `.to_dataframe()`

## Runtime Wiring

- Default backend URL: `http://platform-backend:8080/services` (with local fallbacks)
- Token order: `configure(token=...)`, then `PLATFORM_TOKEN` / `PORTAL_TOKEN`, then token file
- JupyterHub: token refresh via hub `/api/portal-token`

## Public API

```python
from mip import (
    configure,
    catalog,
    Context,
    Analysis,
    Rule,
    FilterGroup,
    Case,
    Validation,
    MISSING,
    Report,
    ReportSection,
)
```

### 1) Configuration

```python
configure(
    base_url="http://localhost:8080/services",
    token="<bearer-token>",
)
```

`configure()` must be called before `catalog` or `Analysis` use.

### 2) Catalog discovery (pre-Context)

```python
catalog.models().to_dataframe()
catalog.datasets("stroke:1.0").to_dataframe()
catalog.get("stroke:1.0")
catalog.visualize("stroke:1.0", include_variables=True)
catalog.visualize_all()
```

### 3) Context and Analysis

```python
context = Context(
    data_model="stroke:1.0",
    datasets=["ssrdataset_harmonized"],
    mip_version="dev",
)

analysis = Analysis(context)
```

### 4) Transformations and cohorts

```python
cohort = analysis.transformations.categorical_from_filters(
    name="stroke_territory_cohort",
    label="Stroke territory cohort",
    cases=[
        Case(label="ACS", when=FilterGroup.and_(Rule("stroke_territory", "in", ["anterior_left"]))),
    ],
    otherwise=MISSING,
    validation=Validation(mutually_exclusive=True, allow_unmatched=True),
)

analysis = analysis.with_transformations([cohort])
cohort_check = analysis.cohorts.validate(
    group_by="stroke_territory_cohort",
    expected_levels=["ACS", "PCS"],
    checks=["counts", "missing"],
)
```

### 5) Descriptive statistics

```python
analysis.describe.numeric(variables=["age"], group_by="stroke_territory_cohort", levels=["ACS", "PCS"])
analysis.describe.categorical(variables=["sex"], group_by="stroke_territory_cohort", levels=["ACS", "PCS"])
```

### 6) Statistical tests

```python
analysis.tests.ttest_independent(
    variables=["age"],
    group_by="stroke_territory_cohort",
    group_a="ACS",
    group_b="PCS",
)
analysis.tests.chi_squared(factor="stroke_territory_cohort", outcomes=["sex"])
```

`analysis.tests.mann_whitney_u(...)` raises `NotImplementedError` until the backend algorithm exists.

### 7) Models

```python
logit = analysis.models.logistic_regression(
    outcome="good_outcome_3m",
    positive_class="good",
    predictors=["age", "sex"],
    reference_levels={"sex": "female"},
    missing="drop",
)
logit.summary().to_dataframe()
logit.metrics().to_dataframe()
```

### 8) Filters

```python
FilterGroup.and_(Rule("age", ">", 60), Rule("sex", "==", "female"))
```

Operators: `==`, `!=`, `in`, `not_in`, `>`, `>=`, `<`, `<=`, `is_null`, `not_null`.

### 9) Reports

```python
report = Report(title="Analysis", sections=[ReportSection(title="Cohort", result=cohort_check)])
report.display()
```

## Error Handling

- `MipConfigurationError`: `configure()` not called
- `MipBackendError`: transient experiment failure
- `MipValidationError`: invalid transformation/cohort input
- `LookupError`: ambiguous or missing data model in `catalog`

## Validation

1. `cd python-client && poetry run python -m unittest discover -s tests -p "test_*.py"`
2. `python3 python-client/verify_script.py`
3. Smoke against `mip/deployment/dev` when backend is available

## Scope Boundary

- `mip-jupyter`: notebook images + Python client
- `platform-backend`: API gateway and experiment orchestration
- `exaflow`: internal execution engine
- No dataset upload or CSV loading APIs in the notebook client
