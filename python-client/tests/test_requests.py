import unittest

from mip import Context
from mip import FilterGroup
from mip import Rule
from mip._requests import build_transient_payload
from mip.filters import Case
from mip.transformations import CategoricalFromFilters


class TestRequests(unittest.TestCase):
    def test_build_transient_payload_includes_preprocessing_and_filters(self):
        transformation = CategoricalFromFilters(
            name="stroke_territory_cohort",
            label="Stroke territory cohort",
            cases=[
                Case(
                    label="ACS",
                    when=FilterGroup.and_(Rule("stroke_territory", "in", ["anterior_left"])),
                )
            ],
        )
        context = Context(
            data_model="stroke:1.0",
            datasets=["ssrdataset_harmonized"],
            filters=FilterGroup.and_(Rule("age", ">", 18)),
            transformations=[transformation],
        )
        payload = build_transient_payload(
            name="Describe",
            algorithm_name="describe",
            context=context,
            y=["age"],
            missing="drop",
            missing_variables=["age"],
        )
        self.assertEqual(payload["algorithm"]["name"], "describe")
        self.assertIn("categorical_from_filters", payload["algorithm"]["preprocessing"])
        self.assertIn("missing_values_handler", payload["algorithm"]["preprocessing"])
        self.assertEqual(
            payload["algorithm"]["inputdata"]["filters"]["rules"][0]["operator"],
            "greater",
        )


if __name__ == "__main__":
    unittest.main()
