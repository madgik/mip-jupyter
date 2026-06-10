import unittest
from unittest.mock import patch

from mip import Analysis
from mip import Context
from mip import configure


class TestTestsNamespace(unittest.TestCase):
    def setUp(self):
        configure(base_url="http://mock-backend", token="mock-token")

    @patch("mip._requests.run_transient")
    def test_ttest_independent_batches_variables(self, mock_run):
        mock_run.return_value = (
            {"t_stat": 1.2, "df": 10, "p": 0.03, "mean_diff": 1.0, "se_diff": 0.5, "ci_lower": -1.0, "ci_upper": 2.0, "cohens_d": 0.4},
            "job-1",
            "success",
        )
        analysis = Analysis(Context(data_model="stroke:1.0", datasets=["ds1"]))
        result = analysis.tests.ttest_independent(
            variables=["age", "nihss_24h"],
            group_by="stroke_territory_cohort",
            group_a="ACS",
            group_b="PCS",
        )
        self.assertEqual(len(result.to_dataframe()), 2)
        self.assertEqual(mock_run.call_count, 2)

    def test_mann_whitney_raises_not_implemented(self):
        analysis = Analysis(Context(data_model="stroke:1.0", datasets=["ds1"]))
        with self.assertRaises(NotImplementedError):
            analysis.tests.mann_whitney_u(
                variables=["age"],
                group_by="stroke_territory_cohort",
                group_a="ACS",
                group_b="PCS",
            )


if __name__ == "__main__":
    unittest.main()
