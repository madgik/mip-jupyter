import os
import sys

sys.path.append(os.getcwd())

print("Importing mip...", flush=True)
try:
    from mip import Analysis, Context, catalog, configure
    print("Import successful.", flush=True)
except Exception as exc:
    print(f"Import failed: {exc}", flush=True)
    sys.exit(1)

print("Configuring client...", flush=True)
configure(base_url="http://mock-backend", token="mock-token")
print("Client configured.", flush=True)

from unittest.mock import MagicMock
from unittest.mock import patch

MOCK_DATA_MODELS = [
    {
        "code": "stroke",
        "version": "1.0",
        "label": "Stroke",
        "longitudinal": False,
        "variables": [],
        "groups": [],
        "datasets": [{"code": "ds1", "label": "Dataset 1"}],
        "datasetsVariables": {},
    }
]

print("Testing catalog path...", flush=True)
with patch("mip.data_model.get_client") as mock_get_client:
    client = MagicMock()
    client.get.return_value = MOCK_DATA_MODELS
    mock_get_client.return_value = client

    models = catalog.models(client=client).to_dataframe()
    if len(models) != 1 or models.loc[0, "name"] != "stroke:1.0":
        print("Catalog smoke test FAILED", flush=True)
        sys.exit(1)
print("Catalog smoke test PASSED", flush=True)

print("Testing Analysis describe path...", flush=True)
with patch("mip._requests.run_transient") as mock_run:
    mock_run.return_value = (
        {
            "featurewise": [
                {
                    "variable": "age",
                    "dataset": "all datasets",
                    "data": {"num_dtps": 10, "num_na": 0, "num_total": 10, "mean": 65.0},
                }
            ]
        },
        "job-1",
        "success",
    )
    context = Context(data_model="stroke:1.0", datasets=["ds1"])
    analysis = Analysis(context)
    result = analysis.describe.numeric(variables=["age"])
    frame = result.to_dataframe()
    if len(frame) == 1 and frame.loc[0, "variable"] == "age":
        print("Analysis smoke test PASSED", flush=True)
    else:
        print("Analysis smoke test FAILED", flush=True)
        sys.exit(1)
