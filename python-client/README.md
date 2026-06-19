# MIP Python client

Notebook-facing library for MIP federated analysis via platform-backend experiments.

## Install

```bash
poetry install
```

Or:

```bash
python3 -m pip install -e .
```

Optional notebook extras:

```bash
poetry install --with notebook
```

## API overview

| Object | Purpose |
|--------|---------|
| `Client` | Owns backend transport and creates catalog/algorithm/experiment facades |
| `ExperimentRegistry` | Lists, reads, and deletes persisted experiments |
| `Catalog` | Discovers data models, variables, and datasets |
| `AnalysisSet` | Holds selected data model, datasets, and variables |
| `Pipeline` | Applies filters/preprocessing and executes named algorithms |
| `F` | Builds backend-compatible filter expressions |
| `MissingValuesHandler`, `OutlierWinsorizer` | Build preprocessing payloads |
| `Result`, `ModelResult` | Wrap raw backend results and logistic-regression sklearn export |
| `mip.sklearn` | Builds sklearn estimators from supported backend model output |

## Removed old API

The MVP is a strict replacement. Legacy notebook APIs such as `configure`, `Context`, namespace `Analysis`, and `ResultTable` are no longer part of this package.

## Test

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
