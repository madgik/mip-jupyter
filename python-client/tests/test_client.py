import unittest
from unittest.mock import patch, MagicMock
from platform_backend_client import Experiment, configure
from platform_backend_client.client import PortalClient
import requests

class TestExperiment(unittest.TestCase):
    def setUp(self):
        configure(base_url="http://mock-backend", token="mock-token")

    @patch('platform_backend_client.client.requests.Session.get')
    def test_list_experiments(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"experiments":[]}'
        mock_response.json.return_value = {
            "experiments": [
                {"uuid": "123", "name": "Test Exp", "status": "DONE"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        exps = Experiment.list()
        self.assertEqual(len(exps), 1)
        self.assertEqual(exps[0].uuid, "123")
        self.assertEqual(exps[0].name, "Test Exp")

    @patch('platform_backend_client.client.requests.Session.post')
    def test_create_experiment(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"uuid":"456"}'
        mock_response.json.return_value = {"uuid": "456", "name": "New Exp", "status": "PENDING"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        exp = Experiment.create(
            name="New Exp",
            algorithm_name="linear_regression",
            data_model="dementia:0.1",
            datasets=["edsd"],
            y=["alzheimer_broad_category"],
            x=["gender"]
        )
        
        self.assertEqual(exp.uuid, "456")
        self.assertEqual(exp.name, "New Exp")
        
        # Verify payload structure
        args, kwargs = mock_post.call_args
        payload = kwargs['json']
        self.assertEqual(payload['name'], "New Exp")
        self.assertEqual(payload['algorithm']['name'], "linear_regression")
        self.assertEqual(payload['algorithm']['inputdata']['y'], ["alzheimer_broad_category"])

    @patch('platform_backend_client.client.requests.Session.post')
    def test_run_transient_experiment(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"uuid":"789"}'
        mock_response.json.return_value = {"uuid": "789", "name": "Quick", "status": "success", "result": {"ok": True}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        exp = Experiment.run_transient(
            name="Quick",
            algorithm_name="descriptive_stats",
            data_model="dementia:0.1",
            datasets=["edsd"],
            y=["alzheimer_broad_category"],
            x=[],
        )

        self.assertEqual(exp.uuid, "789")
        self.assertEqual(exp.status, "success")
        self.assertEqual(exp.results, {"ok": True})

        args, kwargs = mock_post.call_args
        self.assertTrue(args[0].endswith("/experiments/transient"))
        payload = kwargs["json"]
        self.assertEqual(payload["name"], "Quick")
        self.assertEqual(payload["algorithm"]["name"], "descriptive_stats")

class TestPortalClientBaseUrlResolution(unittest.TestCase):
    @patch("platform_backend_client.client.socket.getaddrinfo")
    def test_prefers_localhost_when_compose_host_is_unresolvable(self, mock_getaddrinfo):
        def side_effect(host, _port):
            if host in ("platform-backend", "platform-backend-service"):
                raise OSError("unresolvable")
            return [(None, None, None, None, None)]

        mock_getaddrinfo.side_effect = side_effect
        client = PortalClient(token="mock-token")
        self.assertEqual(client.base_url, "http://localhost:8080/services")

    @patch("platform_backend_client.client.requests.Session.get")
    @patch("platform_backend_client.client.socket.getaddrinfo")
    def test_falls_back_to_next_candidate_on_connection_error(self, mock_getaddrinfo, mock_get):
        def resolve_side_effect(host, _port):
            if host == "platform-backend-service":
                raise OSError("unresolvable")
            return [(None, None, None, None, None)]

        mock_getaddrinfo.side_effect = resolve_side_effect

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"experiments":[]}'
        mock_response.json.return_value = {"experiments": []}
        mock_response.raise_for_status.return_value = None

        mock_get.side_effect = [
            requests.exceptions.ConnectionError(
                "Failed to resolve 'platform-backend' (NameResolutionError)"
            ),
            mock_response,
        ]

        client = PortalClient(token="mock-token")
        payload = client.get("/experiments", params={"size": 10, "page": 0})

        self.assertEqual(payload, {"experiments": []})
        self.assertEqual(client.base_url, "http://localhost:8080/services")
        first_url = mock_get.call_args_list[0].args[0]
        second_url = mock_get.call_args_list[1].args[0]
        self.assertTrue(first_url.startswith("http://platform-backend:8080/services"))
        self.assertTrue(second_url.startswith("http://localhost:8080/services"))


if __name__ == '__main__':
    unittest.main()
