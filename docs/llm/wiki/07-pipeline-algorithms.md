# Pipeline Algorithms — Catalog and Examples

**Read when:** The user asks which algorithms exist, how to call them, or wants a minimal runnable example in MIP Jupyter.

**Skip if:** Stroke-specific inference rules are enough (`recipes/stroke-analysis.md`).

## Pipeline catalog

The mip client exposes **30** typed `Pipeline` methods and **4** preprocessing builders. Registry source of truth: `python-client/mip/catalog_registry.py` (`PIPELINE_BACKEND_ALGORITHMS`).

Discover at runtime:

```python
pipeline.available_algorithms()
client.algorithms().list()   # platform catalog metadata
pipeline.recommend_algorithms()
```

Runnable full-stack script (Stroke 3.7 / SSR, all methods + preprocessing): `workspace/examples/algorithm_examples.py`

### Preprocessing

| Backend step | Wrapper |
|--------------|---------|
| `missing_values_handler` | `MissingValuesHandler` |
| `outlier_winsorizer` | `OutlierWinsorizer` |
| `categorical_column_creator` | `CategoricalColumnCreator` |
| `longitudinal_transformer` | `LongitudinalTransformer` |

Longitudinal workflows: `Pipeline(..., longitudinal=LongitudinalTransformer(visit1=..., visit2=..., strategies={...}))`

### Methods

Call typed methods directly — there is no `Pipeline.run()`. Default `mode="transient"`; use `mode="persisted"` only when saving an experiment.

| Pipeline method | Backend name | Purpose |
|-----------------|--------------|---------|
| `describe()` | `describe` | Summary stats and coverage per variable |
| `histogram(variable=..., bins=...)` | `histogram` | Binned counts for one variable |
| `t_test(variable=..., group_by=..., group_a=..., group_b=...)` | `ttest_independent` | Two-group comparison |
| `one_sample_t_test(variable=..., mu=...)` | `ttest_onesample` | One-sample t-test |
| `paired_t_test(measurement_1=..., measurement_2=...)` | `ttest_paired` | Paired measurements |
| `chi_square_test(x=..., y=...)` | `chi_squared` | Categorical association |
| `fisher_exact(x=..., y=...)` | `fisher_exact` | 2×2 exact test |
| `pearson_correlation(x=..., y=...)` | `pearson_correlation` | Linear correlation |
| `quartiles(variable=...)` | `quartiles` | Quartile summary |
| `anova_oneway(group_by=..., outcome=...)` | `anova_oneway` | One-way ANOVA |
| `anova_twoway(factor_a=..., factor_b=..., outcome=...)` | `anova_twoway` | Two-way ANOVA |
| `mann_whitney_u_test(...)` | `binned_mann_whitney_u_test` | Non-parametric two-group test |
| `outlier_report(variables=..., strategies=...)` | `outlier_report` | Outlier bounds per variable |
| `linear_regression(x=[...], y=...)` | `linear_regression` | OLS regression |
| `linear_regression_cv(x=[...], y=..., n_splits=...)` | `linear_regression_cv` | Cross-validated OLS |
| `logistic_regression(x=[...], y=..., positive_class=...)` | `logistic_regression` | Binary logistic model |
| `logistic_regression_cv(...)` | `logistic_regression_cv` | Cross-validated logistic |
| `cox_regression_classical(time=..., event_var=..., covariates=[...])` | `cox_regression_classical` | Cox proportional hazards |
| `cox_regression_stacked(...)` | `cox_regression_stacked` | Stacked Cox model |
| `lmm(outcome=..., covariates=[...], grouping_var=[...])` | `lmm` | Linear mixed model |
| `glmm_binary(...)` | `glmm_binary` | Binary GLMM |
| `glmm_ordinal(...)` | `glmm_ordinal` | Ordinal GLMM |
| `linear_svm(features=[...], target=...)` | `linear_svm` | Linear SVM |
| `kmeans(features=[...], k=...)` | `kmeans` | K-means clustering |
| `pca(variables=[...])` | `pca` | Principal components |
| `pca_with_transformation(variables=[...])` | `pca_with_transformation` | PCA with transforms |
| `naive_bayes_gaussian(features=[...], target=...)` | `naive_bayes_gaussian` | Gaussian NB |
| `naive_bayes_categorical(features=[...], target=...)` | `naive_bayes_categorical` | Categorical NB |
| `naive_bayes_gaussian_cv(...)` | `naive_bayes_gaussian_cv` | CV Gaussian NB |
| `naive_bayes_categorical_cv(...)` | `naive_bayes_categorical_cv` | CV categorical NB |

### Maintaining the catalog

When the platform adds an algorithm or preprocessing step:

1. Add the mapping to `PIPELINE_BACKEND_ALGORITHMS` in `catalog_registry.py`.
2. Implement the method in `pipeline_algorithms.py`.
3. For preprocessing, add a class in `preprocessing.py` and register it in `PREPROCESSING_STEP_CLASSES`.
4. Run `uv run python -m pytest python-client/tests/test_catalog_registry.py -q`.

## Result keys (common algorithms)

| Algorithm | `result.summary()` highlights |
|-----------|-------------------------------|
| Describe | `featurewise[].data.num_dtps`, `.mean`, `.std` |
| Histogram | `histogram[0].bins`, `histogram[0].counts` |
| T-test | `t_stat`, **`p`**, `mean_diff`, `cohens_d`, `ci_lower`, `ci_upper` |
| Chi-square | `chi2`, **`p_value`**, `dof` |
| Logistic | `indep_vars`, `summary.coefficients`, `summary.lower_ci`, `summary.upper_ci`, `summary.pvalues` |
| Pearson | `correlation`, `p_value` (when supported) |

Other methods: see compact summaries in `algorithm_examples.py` (`summarize()`).

## Rules

- Federated aggregates only — no `inputdata()`, `to_frame()`, or local sklearn on rows.
- Pass **creators** in `new_columns=[poor]`; use `poor.variable` in algorithms.
- Filter enumeration values are often **codes** (`"0"`, `"1"`), not display labels.
- For stroke work, run `scratch/stroke_preflight.py` before inference-heavy scripts.

**Next file:** `workspace/examples/algorithm_examples.py`, or `02-analysis-workflow.md` for the full pipeline pattern.
