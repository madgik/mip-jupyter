# Federated Stroke Pathology — Recipe

**Read when:** Building or extending a federated stroke pathology analysis notebook.

**Skip if:** General MIP onboarding is enough (`01-onboarding.md`). For generic API syntax see `03-mip-client-api.md`.

**This document does not contain a final notebook implementation** — it captures confirmed patterns from existing examples.

## Data model and dataset

```python
client = mip.Client.from_env()
catalog = client.catalog()
dm = catalog.data_model("Stroke", version="3.7")
ssr = dm.datasets["SSR"]
```

Inspect variables: `dm.tree(include_variables=True)`, `dm.variables.search("NIHSS")`.

## Variable selection

Select explicit variable objects before creating the analysis set:

```python
selected_variables = [
    dm.variables["Age"],
    dm.variables["NIHSS 24h"],
    dm.variables["Biological sex"],
    # add stroke-specific variables from catalog labels
]

analysis_set = mip.AnalysisSet(
    data_model=dm,
    datasets=[ssr],
    variables=selected_variables,
)
```

## Cohort creation

Use `CategoricalColumnCreator` for territory or pathology cohorts:

```python
from mip.filters import F
from mip.preprocessing import CategoricalColumnCreator

stroke_territory_cohort = CategoricalColumnCreator(
    label="Stroke Territory",
    rules={
        "ACS": F(territory_var).isin(["ACS"]),
        "PCS": F(territory_var).isin(["PCS"]),
    },
    default_enumeration="Other",
)

cohort_var = stroke_territory_cohort.variable
```

Reference `cohort_var` (not just the code string) in downstream algorithms.

## Pipeline example

```python
from mip.preprocessing import MissingValuesHandler, OutlierWinsorizer

pipeline = mip.Pipeline(
    analysis_set=analysis_set,
    filters=F(age).is_not_null(),
    handle_missing=MissingValuesHandler(strategies={age: "median", nihss_24h: "median"}),
    outlier_handling=OutlierWinsorizer(
        strategies={age: "iqr", nihss_24h: "iqr"},
        tails={age: "both", nihss_24h: "both"},
        folds={age: 1.5, nihss_24h: 1.5},
    ),
    new_columns=[stroke_territory_cohort],
)

pipeline.t_test(
    variable=age,
    group_by=cohort_var,
    group_a="ACS",
    group_b="PCS",
)
pipeline.logistic_regression(x=[age, cohort_var], y=outcome_var, positive_class="1")
```

## Result processing patterns

Examples in `workspace/examples/feres_analysis.ipynb` use helpers to format outputs:

- Histogram: extract `bins`, `counts` from `result.payload`
- T-test: `t_stat`, `df`, `p_value`, `mean_diff`, `ci_lower`, `ci_upper`
- Logistic: `coefficients`, `feature_names`; use `result.to_sklearn()` for local prediction

## Forbidden patterns

- No `.table()` API
- No `Pipeline.run()` — call algorithm methods directly on the pipeline
- No direct Exaflow or backend HTTP from notebook code

## Open questions

Refer to `expected_library.md` when unsure about filter operator support, full missing-value strategy lists, or algorithm parameter validation.

**Next file:** `workspace/examples/feres_analysis.ipynb` for the runnable stroke territory example.
