import unittest

from mip import FilterGroup
from mip import Rule
from mip import Validation
from mip.filters import Case
from mip.transformations import CategoricalFromFilters
from mip.transformations import serialize_transformations


class TestTransformations(unittest.TestCase):
    def test_categorical_from_filters_serializes_for_preprocessing(self):
        transformation = CategoricalFromFilters(
            name="stroke_territory_cohort",
            label="Stroke territory cohort",
            cases=[
                Case(
                    label="ACS",
                    when=FilterGroup.and_(Rule("stroke_territory", "in", ["anterior_left"])),
                )
            ],
            validation=Validation(mutually_exclusive=True, allow_unmatched=True),
        )
        payload = serialize_transformations([transformation])
        self.assertIn("categorical_from_filters", payload)
        variables = payload["categorical_from_filters"]["variables"]
        self.assertEqual(variables[0]["name"], "stroke_territory_cohort")
        self.assertEqual(variables[0]["cases"][0]["label"], "ACS")


if __name__ == "__main__":
    unittest.main()
