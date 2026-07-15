# Federated Stroke Analysis — Recipe

**Read when:** Building or extending a federated stroke analysis, including **novel** or significance-focused workflows.

**Skip if:** General onboarding only (`01-onboarding.md`).

This page is **self-contained** for stroke statistical work. Do not chain `02`/`03`/`04` on startup.

## Novel analysis workflow (default)

When the user asks for a **novel**, **new**, or **significance** stroke analysis on SSR:

1. `read-guide --page recipes/stroke-analysis --topic "novel"` — **first action**
2. `mip-data-model-summary stroke --version 3.7` (bounded metadata)
3. `python scratch/stroke_preflight.py` — **stop** if required variables fail
4. **Pre-specify** one primary hypothesis (outcome, predictors, SSR-only) before running tests
5. `jupyter-mcp scratch-copy-template scratch/<name>.py --source examples/algorithm_examples.py`
6. Trim to one hypothesis; edit with `scratch-append-lines` / `scratch-replace-snippet` only (no heredocs, no shell file writes)
7. Run `python scratch/<name>.py`; save CSVs under `scratch/`
8. `jupyter-mcp scratch-to-notebook scratch/<name>.py scratch/<name>.ipynb --title "<name>"`
9. `notebook-outline`, then `open-file` the notebook
10. Report primary inference: **adjusted logistic regression OR (95% CI)**; label secondary p-values exploratory

Use `notebook-outline workspace/examples/feres_analysis.ipynb` and
`examples/algorithm_examples.py` as pattern references.

### Novel idea guardrails

- One primary outcome (usually poor 3m mRS derived from `"3m mRS good outcome"`)
- Variables must pass preflight — never assume catalog presence means SSR data
- Parenthesize filter rules: `(F(nihss) >= 10) & (F(nihss) < 20)` not `F(nihss) >= 10 & F(nihss) < 20`
- `dm.variables["Age"]` for lookups; `F(age_var)` in filters — never `F("Age")` or `pipeline.get_variable()`
- `AnalysisSet` + `Pipeline(analysis_set=...)` — never `Pipeline(dataset)`
- `MissingValuesHandler(strategies={var: "median"})` — not a bare dict
- Parse logistic results with `parse_logistic_regression_summary()` and report `format_logistic_term()` output

## Discovery (bounded)

```bash
python -m mip_jupyter_dev.jupyter_mcp_cli mip-env-status
python -m mip_jupyter_dev.jupyter_mcp_cli mip-data-model-summary stroke --version 3.7
python -m mip_jupyter_dev.jupyter_mcp_cli mip-search-variables stroke "NIHSS" --version 3.7
```

Do **not** run `python -c` probes, `help(mip)`, env dumps, or `cat` on `.ipynb` JSON.

## Data model and dataset

```python
client = mip.Client.from_env()
dm = client.catalog().data_model("Stroke 3.7")
ssr = dm.datasets["SSR"]
```

Use catalog **labels** with exact match. Filter rules use enumeration **codes** (`"1"`, `"2"`).

## Dataset selection

- **Primary:** `datasets=[ssr]` only — never mix `SSR` with `SSR-even` / `SSR-odd`
- **Sensitivity:** `SSR-even` or `SSR-odd` alone

## Coverage preflight (required)

```bash
python scratch/stroke_preflight.py
```

Variables often **empty in SSR** (exclude from primary models): `"Known AF"`, `"Oral anticoagulation"`, `"Prestroke sleep hours"`.

## Pipeline and algorithms

Call algorithm methods directly — no `Pipeline.run()`.

```python
pipeline = mip.Pipeline(
    analysis_set=mip.AnalysisSet(data_model=dm, datasets=[ssr], variables=selected),
    filters=common_filters,
    handle_missing=common_missing,
    new_columns=[poor_outcome_creator],  # creators, not .variable
)
pipeline.t_test(variable=age, group_by=poor_outcome, group_a="Yes", group_b="No")
pipeline.chi_square_test(x=severity_var, y=poor_outcome)
pipeline.logistic_regression(x=[age, nihss, severity_var], y=poor_outcome, positive_class="Yes")
```

## Result shapes (`result.summary()`)

| Algorithm | Keys |
|-----------|------|
| T-test | `t_stat`, **`p`** (not `p_value`), `mean_diff`, `cohens_d` |
| Chi-square | `chi2`, **`p_value`**, `dof` |
| Logistic | `indep_vars`, `summary.coefficients`, `summary.pvalues`, `summary.lower_ci`, `summary.upper_ci` |

## Interpreting primary logistic regression

- Report **adjusted OR (95% CI)** per predictor using `format_logistic_term()`
- **Categorical terms** (`sex[1]`, severity levels): OR is vs the reference level — state the reference
- **Continuous predictors** (Age, Admission score): OR is per **1-unit** increase on the federated scale
- **Treatment variables** (IVT, EVT): observational associations only — not causal treatment effects
- **Collinearity / sensitivity:** if NIHSS and a derived severity composite diverge in sign, treat as collinearity or model specification — not a biological mechanism
- **McFadden R²** describes model fit; do not use it for causal inference
- Secondary t-test/chi-square p-values are exploratory; disclose uncorrected multiplicity

## Statistical guardrails

1. Pre-specify primary hypothesis before tests
2. Report effect sizes and CIs, not p-values alone
3. Disclose uncorrected multiplicity for secondary comparisons
4. Federated only — no `inputdata()`, `to_frame()`, sklearn on rows

## Reference scripts (patterns, not defaults)

| File | Role |
|------|------|
| `scratch/stroke_preflight.py` | SSR coverage gate (run first; synced at runtime) |
| `examples/algorithm_examples.py` | **Copy and trim** for novel work (`scratch-copy-template`) |
| `examples/feres_analysis.ipynb` | Territory analysis pattern |

## Forbidden patterns

- Heredocs / `write_stdin` / `cat > scratch/*.py` / giant `python -c`
- `pipeline.get_variable()`, `describe([vars])`, `F("label")` strings
- `inputdata()`, `to_frame()`, local sklearn/PCA
- `new_columns=[creator.variable]` — pass the **creator**
- Ending with CSVs only — always transfer to `scratch/<name>.ipynb`

**Next:** `jupyter-mcp scratch-copy-template scratch/<name>.py --source examples/algorithm_examples.py` after preflight passes.
