import unittest

from mip import FilterGroup
from mip import Rule


class TestFilters(unittest.TestCase):
    def test_rule_serializes_to_backend_format(self):
        payload = Rule("stroke_territory", "in", ["anterior_left"]).to_dict()
        self.assertEqual(payload["id"], "stroke_territory")
        self.assertEqual(payload["operator"], "in")
        self.assertEqual(payload["value"], ["anterior_left"])

    def test_filter_group_and_serializes_nested_rules(self):
        payload = FilterGroup.and_(
            Rule("stroke_territory", "in", ["anterior_left"]),
            Rule("age", ">=", 18),
        ).to_dict()
        self.assertEqual(payload["condition"], "AND")
        self.assertEqual(len(payload["rules"]), 2)
        self.assertEqual(payload["rules"][1]["operator"], "greater_or_equal")

    def test_notebook_operators_map_to_backend(self):
        self.assertEqual(Rule("x", "==", "a").to_dict()["operator"], "equal")
        self.assertEqual(Rule("x", "!=", "a").to_dict()["operator"], "not_equal")
        self.assertEqual(Rule("x", "not_null").to_dict()["operator"], "is_not_null")


if __name__ == "__main__":
    unittest.main()
