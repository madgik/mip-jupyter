import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from mip.exceptions import UnsupportedOperationError
from mip.results import ModelResult
from mip.results import Result
from mip.results import _histogram_data


class TestResults(unittest.TestCase):
    def test_summary_returns_raw(self):
        result = Result(raw={"a": 1}, payload={"result": {"a": 1}})
        self.assertEqual(result.summary(), {"a": 1})
        self.assertEqual(result.raw, {"a": 1})
        self.assertEqual(result.payload, {"result": {"a": 1}})

    def test_plot_raises_for_non_plot_result(self):
        with self.assertRaises(UnsupportedOperationError):
            Result(raw={}, result_type="describe").plot()

    def test_histogram_data_reads_list_payload(self):
        data = _histogram_data({"histogram": [{"var": "age", "bins": [1, 2, 3], "counts": [4, 5]}]})
        self.assertEqual(data, ([1, 2, 3], [4, 5]))

    def test_histogram_highlights_and_to_frame(self):
        result = Result(
            raw={"variable": "Age", "bins": [40, 50, 60], "counts": [10, 20, 5]},
            result_type="histogram",
        )
        highlights = result.highlights()
        self.assertEqual(highlights["bins"], 3)
        self.assertEqual(highlights["total_count"], 35.0)
        frame = result.to_frame()
        self.assertEqual(frame["bin"].tolist(), [40, 50, 60])
        self.assertEqual(frame["count"].tolist(), [10, 20, 5])
        html = result._repr_html_()
        self.assertIn("Preview", html)
        self.assertIn("histogram", html.lower())
        self.assertIn(".plot()", html)

    def test_describe_to_frame(self):
        result = Result(
            raw={
                "featurewise": [
                    {
                        "variable": "Age",
                        "dataset": "ADNI",
                        "data": {"num_dtps": 100, "mean": 72.5, "std": 8.1, "min": 50, "max": 90},
                    }
                ]
            },
            result_type="describe",
        )
        frame = result.to_frame()
        self.assertEqual(frame.iloc[0]["variable"], "Age")
        self.assertEqual(frame.iloc[0]["n"], 100)
        self.assertIn("Age", result._repr_html_())

    def test_t_test_highlights(self):
        result = Result(
            raw={"t_stat": 2.1, "p": 0.04, "mean_diff": 1.5, "cohens_d": 0.3},
            result_type="t_test",
        )
        highlights = result.highlights()
        self.assertEqual(highlights["p"], 0.04)
        frame = result.to_frame()
        self.assertEqual(frame.iloc[0]["t_stat"], 2.1)

    def test_chi_square_to_frame(self):
        result = Result(raw={"chi2": 9.2, "p_value": 0.002, "dof": 2}, result_type="chi_square_test")
        frame = result.to_frame()
        self.assertEqual(frame.iloc[0]["chi2"], 9.2)
        self.assertEqual(frame.iloc[0]["p_value"], 0.002)

    def test_logistic_to_frame_and_model_card(self):
        result = ModelResult(
            raw={
                "summary": {
                    "n_obs": 200,
                    "feature_names": ["Intercept", "Age", "Sex"],
                    "coefficients": [0.1, 0.2, -0.3],
                    "pvalues": [0.5, 0.01, 0.2],
                    "lower_ci": [-0.1, 0.05, -0.6],
                    "upper_ci": [0.3, 0.35, 0.0],
                }
            },
            result_type="logistic_regression",
        )
        self.assertEqual(result.highlights()["n_obs"], 200)
        frame = result.to_frame()
        self.assertEqual(frame["feature"].tolist(), ["Intercept", "Age", "Sex"])
        self.assertEqual(frame.iloc[1]["p"], 0.01)
        html = result._repr_html_()
        self.assertIn("Age", html)
        self.assertIn(".to_sklearn()", html)

    def test_to_frame_raises_when_unsupported(self):
        with self.assertRaises(UnsupportedOperationError):
            Result(raw={"opaque": True}, result_type="kmeans").to_frame()

    def test_plot_labels_histogram(self):
        result = Result(
            raw={"variable": "MMSE", "bins": ["a", "b"], "counts": [3, 7]},
            result_type="histogram",
        )
        axis = MagicMock()
        figure = MagicMock()
        with patch("matplotlib.pyplot.subplots", return_value=(figure, axis)):
            returned = result.plot()
        self.assertIs(returned, axis)
        axis.bar.assert_called_once()
        axis.set_ylabel.assert_called_with("count")
        axis.set_xlabel.assert_called_with("MMSE")
        axis.set_title.assert_called_with("Histogram: MMSE")
        figure.tight_layout.assert_called_once()


if __name__ == "__main__":
    unittest.main()
