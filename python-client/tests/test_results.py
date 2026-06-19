import unittest

from mip.exceptions import UnsupportedOperationError
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


if __name__ == "__main__":
    unittest.main()
