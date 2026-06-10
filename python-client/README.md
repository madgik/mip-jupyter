# MIP Python client

Notebook-facing library for MIP federated analysis via platform-backend transient experiments.

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

| Module | Purpose |
|--------|---------|
| `catalog` | List data models, datasets, visualize metadata (before `Context`) |
| `Context` | Immutable analysis state (`data_model`, `datasets`, filters, transformations) |
| `Analysis` | `transformations`, `cohorts`, `describe`, `tests`, `models` namespaces |
| `configure` | Set platform-backend URL and token |

## Test

```bash
poetry run python -m unittest discover -s tests -p "test_*.py"
```
