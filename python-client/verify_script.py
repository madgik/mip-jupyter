import sys
import os
sys.path.append(os.getcwd())

print("Importing platform_backend_client...", flush=True)
try:
    from platform_backend_client import Experiment, configure
    print("Import successful.", flush=True)
except Exception as e:
    print(f"Import failed: {e}", flush=True)
    sys.exit(1)

print("Configuring client...", flush=True)
configure(base_url="http://mock-backend", token="mock-token")
print("Client configured.", flush=True)

from unittest.mock import MagicMock, patch

print("Testing list experiments...", flush=True)
with patch('platform_backend_client.client.requests.Session.get') as mock_get:
    mock_response = MagicMock()
    mock_response.json.return_value = {"experiments": [{"uuid": "123", "name": "Test Exp", "status": "DONE"}]}
    mock_get.return_value = mock_response

    exps = Experiment.list()
    print(f"Found {len(exps)} experiments.", flush=True)
    if len(exps) == 1 and exps[0].uuid == "123":
        print("List experiments test PASSED", flush=True)
    else:
        print("List experiments test FAILED", flush=True)

print("Testing create experiment...", flush=True)
with patch('platform_backend_client.client.requests.Session.post') as mock_post:
    mock_response = MagicMock()
    mock_response.json.return_value = {"uuid": "456", "name": "New Exp", "status": "PENDING"}
    mock_post.return_value = mock_response

    exp = Experiment.create(
        name="New Exp",
        algorithm_name="linear_regression",
        data_model="dementia:0.1",
        datasets=["edsd"],
        y=["alzheimer_broad_category"]
    )
    
    print(f"Created experiment {exp.uuid}", flush=True)
    if exp.uuid == "456":
        print("Create experiment test PASSED", flush=True)
    else:
        print("Create experiment test FAILED", flush=True)
