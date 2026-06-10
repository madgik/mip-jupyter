import unittest
from unittest.mock import patch

from mip import Analysis
from mip import Context
from mip import configure


LOGISTIC_RESULT = {
    "dependent_var": "good_outcome_3m",
    "indep_vars": ["age"],
    "summary": {
        "n_obs": 100,
        "coefficients": [0.1, 0.5],
        "stderr": [0.2, 0.1],
        "lower_ci": [-0.1, 0.3],
        "upper_ci": [0.3, 0.7],
        "z_scores": [0.5, 5.0],
        "pvalues": [0.6, 0.01],
        "df_model": 1,
        "df_resid": 98,
        "r_squared_cs": 0.1,
        "r_squared_mcf": 0.2,
        "ll0": -50.0,
        "ll": -45.0,
        "aic": 94.0,
        "bic": 99.0,
    },
}


class TestModels(unittest.TestCase):
    def setUp(self):
        configure(base_url="http://mock-backend", token="mock-token")

    @patch("mip._requests.run_transient")
    def test_logistic_regression_parses_summary_and_metrics(self, mock_run):
        mock_run.return_value = (LOGISTIC_RESULT, "job-1", "success")
        analysis = Analysis(Context(data_model="stroke:1.0", datasets=["ds1"]))
        result = analysis.models.logistic_regression(
            outcome="good_outcome_3m",
            positive_class="good",
            predictors=["age"],
        )
        summary = result.summary().to_dataframe()
        metrics = result.metrics().to_dataframe()
        self.assertIn("coefficient", summary.columns)
        self.assertEqual(metrics.loc[0, "n_obs"], 100)


if __name__ == "__main__":
    unittest.main()
