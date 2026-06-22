# LLM Agent Wiki for `mip-jupyter`

This wiki is an onboarding guide for small or local coding agents working in `mip-jupyter`. It is optimized for agents that may struggle with long prompts or large context windows.

Read this after `AGENTS.md`.

## 1. What this repository is

`mip-jupyter` contains two related deliverables:

1. Docker images for Jupyter and JupyterHub environments.
2. The notebook-facing `mip` Python client used by analysts to run federated analyses through `platform-backend`.

The client is not a data-access library. It is a thin federated-analysis client. Analysts discover metadata, select authorized datasets and variables, then execute backend-approved aggregate algorithms.

Important files:

- `README.md` - setup and quick start.
- `expected_library.md` - public API contract.
- `Welcome.ipynb` - runnable API walkthrough.
- `feres_analysis.ipynb` - stroke territory example.
- `python-client/mip/` - client implementation.
- `python-client/tests/` - mocked tests.

## 2. Mental model for the `mip` client

The flow is always:

```text
Client -> Catalog -> DataModel -> Dataset/Variable selection -> AnalysisSet -> Pipeline -> Algorithm result
```

The pipeline execution order is fixed:

```text
AnalysisSet selection -> filters -> missing-value handling -> outlier handling -> derived columns -> algorithm
```

Do not reorder this flow. Do not invent a generic runner. Use the explicit methods on `AnalysisSet` and `Pipeline`.

## 3. Safe imports

Use this import block in notebooks unless a task proves more imports are needed:

```python
import mip
from mip.filters import F
from mip.preprocessing import (
    CategoricalColumnCreator,
    MissingValuesHandler,
    OutlierWinsorizer,
)
```

Avoid importing private modules from `mip` in notebooks. The public entry points are enough for analyst-facing work.

## 4. Environment setup in notebooks

The standard setup is:

```python
client = mip.Client.from_env()
catalog = client.catalog()
```

`Client.from_env()` reads backend connection details from environment variables such as:

- `PLATFORM_BACKEND_URL` or `MIP_BASE_URL`
- `PLATFORM_TOKEN` or `MIP_TOKEN`
- `PLATFORM_BACKEND_TIMEOUT`
- `PLATFORM_BACKEND_ALLOW_REDIRECTS`

Never hard-code credentials or tokens in a notebook.

## 5. Catalog discovery pattern

Start every analysis notebook with discovery. Do not jump directly to a model.

```python
models = catalog.list()
models
```

Useful catalog calls:

```python
catalog.list()
catalog.summaries()
catalog.tree()
```

After selecting a data model code from real output:

```python
dm = catalog.data_model("selected_code")
dm.summary()
dm.datasets.list()
dm.variables.list()
```

Search datasets and variables with real clinical or domain terms:

```python
dm.datasets.search("stroke")
dm.variables.search("stroke")
dm.variables.search("age")
dm.variables.search("outcome")
```

Only use codes that appear in returned metadata.

## 6. Data model, dataset, and variable selection

Use bracket access after discovering actual codes:

```python
dataset = dm.datasets["dataset_code"]
age = dm.variables["age"]
outcome = dm.variables["outcome_code"]
```

Good notebooks explain why each item was selected.

Bad notebooks silently hard-code codes without showing catalog discovery.

## 7. AnalysisSet pattern

An `AnalysisSet` is only a selected scope: one data model, selected datasets, selected variables.

```python
analysis_set = mip.AnalysisSet(
    data_model=dm,
    datasets=[dataset],
    variables=[age, outcome],
)

analysis_set.summary()
analysis_set.explain()
```

For early EDA:

```python
analysis_set.histogram(variable=age, bins=20)
```

Do not expect patient rows. Do not try to pull local data frames.

## 8. Filters

Use `F(variable)` expressions:

```python
adult_filter = F(age) >= 18
non_missing_outcome = F(outcome).is_not_null()
combined = adult_filter & non_missing_outcome
combined.explain()
```

Supported patterns include:

```python
F(age) >= 18
F(age).between(18, 90)
F(outcome).is_not_null()
F(group).isin(["case", "control"])
F(group).not_in(["unknown"])
expr1 & expr2
expr1 | expr2
~expr1
```

Be conservative with string matching helpers unless backend support is confirmed.

## 9. Preprocessing builders

Missing values:

```python
missing = MissingValuesHandler(
    strategies={age: "median", score: "mean"},
)
```

Outlier winsorization:

```python
outliers = OutlierWinsorizer(
    strategies={score: "iqr"},
    tails={score: "both"},
    folds={score: 1.5},
)
```

Variable-object keys serialize to variable codes. String keys also pass through.

## 10. Derived categorical columns

Use `CategoricalColumnCreator` for clinically meaningful categories created from filter rules.

```python
creator = CategoricalColumnCreator(
    code="severity_group",
    rules={
        "mild": F(score) < 5,
        "moderate_or_severe": F(score) >= 5,
    },
    default_enumeration="unclassified",
)

severity_group = creator.variable
severity_group.code
severity_group.categories()
severity_group.metadata()
```

Rules:

- Document the categories in Markdown.
- Use `creator.variable` downstream when appropriate.
- Do not include both source variables and derived variables in the same final model unless justified.
- Keep category rules simple and clinically interpretable.

## 11. Pipeline pattern

```python
pipeline = mip.Pipeline(
    analysis_set=analysis_set,
    filters=combined,
    handle_missing=missing,
    outlier_handling=outliers,
    new_columns=[creator],
)

pipeline.summary()
pipeline.explain()
```

Then run explicit algorithms:

```python
pipeline.describe()
pipeline.histogram(variable=age, bins=20)
```

Do not use `Pipeline.run(...)`. Do not invent generic execution APIs.

## 12. Supported pipeline algorithms

Currently documented algorithm methods:

```python
pipeline.describe()
pipeline.histogram(variable=variable, bins=20)
pipeline.t_test(variable=numeric_variable, group_by=group_variable, group_a="A", group_b="B")
pipeline.pearson_correlation(x=numeric_x, y=numeric_y)
pipeline.chi_square_test(x=categorical_x, y=categorical_y)
pipeline.logistic_regression(x=[x1, x2], y=binary_y, positive_class="case")
```

Use `client.algorithms()` for backend algorithm metadata:

```python
registry = client.algorithms()
registry.list()
registry.search("logistic")
registry.preprocessing()
registry.statistics()
registry.models()
```

## 13. Choosing a statistical method

Use the simplest valid method first.

| Question type | Preferred method when available |
| --- | --- |
| Numeric variable differs between two groups | `pipeline.t_test(...)` |
| Categorical variable associated with categorical outcome | `pipeline.chi_square_test(...)` |
| Numeric variable associated with numeric variable | `pipeline.pearson_correlation(...)` |
| Binary outcome with covariates | `pipeline.logistic_regression(...)` |

Always state the null and alternative hypothesis in Markdown before significance tests.

Avoid causal claims unless the study design supports causality.

## 14. Logistic regression pattern

Use only for a real binary outcome with a known positive class:

```python
logreg = pipeline.logistic_regression(
    x=[age, sex, severity_group],
    y=outcome,
    positive_class="positive_label",
)

logreg.summary()
```

Use Exaflow-style parameter names exactly: `x`, `y`, and `positive_class`.

## 15. sklearn export pattern

Only use sklearn export if the returned result supports it.

```python
if hasattr(logreg, "feature_schema"):
    schema = logreg.feature_schema()
    schema

if hasattr(logreg, "to_sklearn"):
    sklearn_model = logreg.to_sklearn()
    sklearn_model.feature_names_in_
```

Document this clearly:

- The exported model is local, but the training happened through the federated backend.
- Local prediction requires user-preprocessed local data.
- Local input columns must match `sklearn_model.feature_names_in_`.
- The notebook must not implement automatic local preprocessing unless explicitly requested and supported by local data.

## 16. Result handling

`Result` and `ModelResult` expose:

```python
result.summary()
result.raw
result.payload
```

Do not invent fields such as `result.p_value`, `result.coefficients`, or `result.table` unless the backend response actually contains them and the notebook inspects that response safely.

Prefer displaying `summary()` first, then inspect `raw` only when needed.

## 17. Notebook writing rules

Good notebooks:

- Start with catalog exploration.
- Explain each decision before the code that implements it.
- Use real data model/dataset/variable codes discovered from metadata.
- Keep cells executable from top to bottom.
- Use backend-approved aggregate outputs only.
- End with limitations and reproducibility summary.

Bad notebooks:

- Assume a data model code.
- Guess variable codes.
- Try to download patient-level rows.
- Use `.table()`.
- Use `Pipeline.run(...)`.
- Hide important decisions in unexplained code.

## 18. Reproducible analysis notebook template

Use this section order for substantial analyses:

1. Title and objective
2. Setup and imports
3. Catalog and algorithm exploration
4. Data model and dataset selection
5. Variable search and variable selection
6. Research question
7. AnalysisSet definition
8. Initial exploratory analysis
9. Pipeline definition
10. Derived columns, if any
11. Descriptive statistics after filtering/preprocessing
12. Statistical significance testing
13. Modeling, if appropriate
14. sklearn export, only if logistic regression is run and supported
15. Interpretation
16. Limitations
17. Reproducibility summary

The reproducibility summary should include:

- Data model code and version, if available.
- Selected datasets.
- Selected variables.
- Derived variables and enumerations.
- Filters.
- Missing-value strategy.
- Outlier-handling strategy.
- Algorithms executed.
- Outcome and positive class, if applicable.
- sklearn prediction requirements, if applicable.

## 19. Small-agent phased workflow

For local LLMs with limited effective context, split big notebook tasks into phases.

### Phase 1: API reconnaissance

Create or update a small state file, for example `stroke_analysis_state.md`, with confirmed API facts:

- imports
- catalog API
- dataset/variable search API
- `AnalysisSet` API
- `Pipeline` API
- preprocessing API
- algorithms
- forbidden calls
- open questions

### Phase 2: notebook skeleton and catalog exploration

Create notebook sections 1-5 only. Do not model. Search metadata and store candidate outputs.

### Phase 3: research question and AnalysisSet

Add sections 6-8. Select one clinically/statistically valid research question based on actual metadata.

### Phase 4: pipeline and significance tests

Add sections 9-12. Define filters, missing handling, outlier handling, derived variables, and simple significance tests.

### Phase 5: optional modeling and final report

Add sections 13-17. Use logistic regression only when valid. Finish interpretation, limitations, and reproducibility.

### Phase 6: QA

Check top-to-bottom execution, forbidden APIs, patient-level access, fake codes, and reproducibility summary completeness.

## 20. Stroke pathology notebook guidance

For stroke-focused work, begin with metadata searches such as:

```python
search_terms = [
    "stroke",
    "pathology",
    "lesion",
    "imaging",
    "severity",
    "outcome",
    "mortality",
    "recurrence",
    "functional",
    "disability",
    "NIHSS",
    "mRS",
    "infarct",
    "hemorrhage",
    "age",
    "sex",
    "gender",
]

variable_hits = {term: dm.variables.search(term) for term in search_terms}
variable_hits
```

Candidate research questions must be derived from available variables. Examples are only valid if the required variables exist:

- Does a severity score differ by lesion/pathology group?
- Is a pathology or imaging category associated with functional outcome?
- Are age and severity associated with a numeric outcome score?
- Is a binary poor-outcome variable associated with severity, age, sex, and lesion/pathology category?

Do not force a stroke analysis if the catalog does not expose the needed variables.

## 21. Common failure modes and fixes

### Failure: hallucinated codes

Fix: add catalog search cells and replace guessed codes with placeholders or real metadata output.

### Failure: `.table()` call

Fix: remove it. Use `summary()`, `raw`, or backend-supported result display.

### Failure: direct dataframe manipulation of patient rows

Fix: remove it. Use `AnalysisSet` and `Pipeline` aggregate methods.

### Failure: modeling before exploration

Fix: reorder the notebook. Exploration and variable selection must come first.

### Failure: logistic regression on non-binary outcome

Fix: use a simpler method or create a clearly documented binary derived variable if clinically meaningful and supported by metadata.

### Failure: sklearn export without schema check

Fix: call `feature_schema()` first when available, then `to_sklearn()`.

## 22. Testing and validation

Use mocked tests for client code:

```bash
uv run python -m unittest discover -s python-client/tests -p "test_*.py"
uv run python python-client/verify_script.py
```

Without `uv`:

```bash
cd python-client && python3 -m unittest discover -s tests -p "test_*.py"
python3 python-client/verify_script.py
```

Unit tests should patch HTTP transport. They must not require a live platform backend.

## 23. Security reminders

Never commit:

- real tokens
- real backend credentials
- patient-level data
- private output dumps
- environment-specific secrets

Use environment variables for runtime configuration.

## 24. Final checklist for agent-generated notebooks

Before finishing, verify:

- The notebook imports only public APIs.
- Catalog exploration exists before selection.
- All selected codes come from metadata or are clearly marked placeholders.
- No `.table()` appears.
- No `Pipeline.run(...)` appears.
- No patient-level access is attempted.
- All algorithms are called through `AnalysisSet` or `Pipeline`.
- Markdown explains statistical choices.
- Limitations mention federation and aggregate-only outputs.
- Reproducibility summary is complete.
