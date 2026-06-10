import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from mip import Analysis
from mip import Context
from mip import configure


DESCRIBE_RESULT = {
    "featurewise": [
        {
            "variable": "age",
            "dataset": "all datasets",
            "data": {
                "num_dtps": 10,
                "num_na": 2,
                "num_total": 12,
                "mean": 65.0,
                "std": 5.0,
                "q2": 64.0,
            },
        }
    ]
}


class TestDescribe(unittest.TestCase):
    def setUp(self):
        configure(base_url="http://mock-backend", token="mock-token")

    @patch("mip._requests.run_transient")
    def test_numeric_describe_flattens_with_rename(self, mock_run):
        mock_run.return_value = (DESCRIBE_RESULT, "job-1", "success")
        analysis = Analysis(Context(data_model="stroke:1.0", datasets=["ds1"]))
        result = analysis.describe.numeric(
            variables=["age"],
            metrics=["num_dtps", "q2"],
            rename={"num_dtps": "n_non_null", "q2": "approx_median"},
        )
        frame = result.to_dataframe()
        self.assertEqual(frame.loc[0, "n_non_null"], 10)
        self.assertEqual(frame.loc[0, "approx_median"], 64.0)


if __name__ == "__main__":
    unittest.main()
