# Federated Stroke Analysis — Recipe

**Read when:** Federated stroke analysis, including novel / significance work.

**Skip if:** General onboarding only (`01-onboarding.md`).

Self-contained for stroke stats — do not chain `02`/`03`/`04` on startup.

## Novel analysis (default)

1. `read-guide --page recipes/stroke-analysis --topic novel`
2. `mip-data-model-summary stroke --version 3.7`
3. `python scratch/stroke_preflight.py` — **stop** if required vars fail
4. Pre-specify one primary hypothesis (outcome, predictors, SSR-only)
5. `scratch-copy-template scratch/<name>.py --source examples/algorithm_examples.py`
6. Trim/edit with `scratch-append-lines` / `scratch-replace-snippet` only
7. `python scratch/<name>.py`; save CSVs under `scratch/`
8. `scratch-to-notebook` → `notebook-outline` → `open-file`
9. Primary report: **adjusted logistic OR (95% CI)**; secondary p-values exploratory

Patterns: `examples/feres_analysis.ipynb`, `examples/algorithm_examples.py`.

## Guardrails

- One primary outcome (often poor 3m mRS from `"3m mRS good outcome"`)
- Preflight must pass — catalog presence ≠ SSR data
- Parenthesize filters: `(F(nihss) >= 10) & (F(nihss) < 20)`
- `dm.variables["Age"]` + `F(age_var)` — never `F("Age")` / `pipeline.get_variable()`
- `AnalysisSet` + `Pipeline(analysis_set=...)`; `MissingValuesHandler(strategies={...})`
- Parse logistic with `parse_logistic_regression_summary()` / `format_logistic_term()`
- Dataset: `datasets=[ssr]` only — never mix SSR with SSR-even/odd
- Often empty in SSR (exclude primary): `"Known AF"`, `"Oral anticoagulation"`,
  `"Prestroke sleep hours"`

```python
client = mip.Client.from_env()
dm = client.catalog().data_model("Stroke 3.7")
ssr = dm.datasets["SSR"]
pipeline = mip.Pipeline(
    analysis_set=mip.AnalysisSet(data_model=dm, datasets=[ssr], variables=selected),
    filters=common_filters,
    handle_missing=common_missing,
    new_columns=[poor_outcome_creator],
)
pipeline.logistic_regression(x=[age, nihss], y=poor_outcome, positive_class="Yes")
```

Result keys: t-test `p`; chi-square `p_value`; logistic `summary.coefficients` /
`pvalues` / `lower_ci` / `upper_ci`. Effect sizes + CIs over p alone; disclose
multiplicity. No `inputdata()` / `to_frame()` / sklearn on rows.

## Forbidden

Heredocs / `write_stdin` / shell file writes; `new_columns=[creator.variable]`;
ending with CSVs only — always transfer to `scratch/<name>.ipynb`.

**Next:** `scratch-copy-template` after preflight passes.
