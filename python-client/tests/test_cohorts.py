import unittest
from unittest.mock import patch

from mip import Analysis
from mip import Context
from mip import FilterGroup
from mip import Rule
from mip import configure
from mip.filters import Case
from mip.transformations import CategoricalFromFilters


class TestCohorts(unittest.TestCase):
    def setUp(self):
        configure(base_url="http://mock-backend", token="mock-token")

    @patch("mip._requests.run_transient")
    def test_validate_returns_counts_from_describe(self, mock_run):
        mock_run.return_value = (
            {
                "featurewise": [
                    {
                        "variable": "stroke_territory_cohort",
                        "dataset": "all datasets",
                        "data": {
                            "num_na": 1,
                            "counts": {"ACS": 5, "PCS": 4},
                        },
                    }
                ]
            },
            "job-1",
            "success",
        )
        transformation = CategoricalFromFilters(
            name="stroke_territory_cohort",
            label="Cohort",
            cases=[
                Case(label="ACS", when=FilterGroup.and_(Rule("x", "==", "1"))),
                Case(label="PCS", when=FilterGroup.and_(Rule("x", "==", "2"))),
            ],
        )
        context = Context(
            data_model="stroke:1.0",
            datasets=["ds1"],
            transformations=[transformation],
        )
        analysis = Analysis(context)
        result = analysis.cohorts.validate(
            group_by="stroke_territory_cohort",
            expected_levels=["ACS", "PCS"],
            checks=["counts", "missing"],
        )
        frame = result.to_dataframe()
        self.assertEqual(frame.loc[0, "count"], 5)
        self.assertEqual(frame.loc[0, "missing"], 1)


if __name__ == "__main__":
    unittest.main()
