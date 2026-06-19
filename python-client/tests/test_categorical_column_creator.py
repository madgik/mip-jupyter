import unittest

from mip.filters import F
from mip.preprocessing import CategoricalColumnCreator


class Var:
    def __init__(self, code):
        self.code = code


class TestCategoricalColumnCreator(unittest.TestCase):
    def test_categorical_column_creator_creates_derived_variable_with_enumerations(self):
        mmse = Var("mmse")
        cdr = Var("cdr")
        creator = CategoricalColumnCreator(
            code="cognitive_profile",
            rules={
                "preserved": F(mmse) >= 27,
                "mild_impairment": F(mmse).between(20, 26) & F(cdr).isin([0.5, 1.0]),
                "severe_impairment": F(mmse) < 20,
            },
            default_enumeration="unclassified",
        )

        self.assertEqual(creator.variable.code, "cognitive_profile")
        self.assertEqual(
            creator.enumerations,
            ["preserved", "mild_impairment", "severe_impairment", "unclassified"],
        )
        self.assertTrue(creator.variable.is_categorical())
        self.assertFalse(creator.variable.is_numerical())
        self.assertEqual(creator.variable.categories(), creator.enumerations)

    def test_categorical_column_creator_payload_uses_filter_rules_strategy(self):
        mmse = Var("mmse")
        creator = CategoricalColumnCreator(
            code="cognitive_profile",
            rules={"preserved": F(mmse) >= 27},
            default_enumeration="unclassified",
        )

        spec = creator.spec()
        self.assertEqual(spec["name"], "categorical_column_creator")
        self.assertEqual(spec["parameters"]["code"], "cognitive_profile")
        self.assertEqual(spec["parameters"]["strategy"], "filter_rules")
        self.assertEqual(spec["parameters"]["default_enumeration"], "unclassified")
        self.assertEqual(spec["parameters"]["rules"]["preserved"]["operator"], "greater_or_equal")


if __name__ == "__main__":
    unittest.main()
