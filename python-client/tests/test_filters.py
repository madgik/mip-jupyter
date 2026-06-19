import unittest
from types import SimpleNamespace

from mip.filters import F


class TestFilters(unittest.TestCase):
    def test_operator_serializes_variable_code(self):
        age = SimpleNamespace(code="age")
        payload = (F(age) >= 50).explain()
        self.assertEqual(payload["field"], "age")
        self.assertEqual(payload["operator"], "greater_or_equal")
        self.assertEqual(payload["value"], 50)

    def test_methods_and_composition(self):
        expr = (F("mmse").is_not_null() & F("sex").isin(["M", "F"])) | ~F("diagnosis").isin(["AD"])
        payload = expr.explain()
        self.assertEqual(payload["condition"], "OR")
        self.assertEqual(payload["rules"][0]["condition"], "AND")
        self.assertEqual(payload["rules"][1]["operator"], "not_in")
        self.assertEqual(payload["rules"][1]["value"], ["AD"])

    def test_between_and_to_payload(self):
        age = SimpleNamespace(code="age")
        expr = F(age).between(20, 26)
        payload = expr.to_payload()
        self.assertEqual(payload["operator"], "between")
        self.assertEqual(payload["value"], [20, 26])


if __name__ == "__main__":
    unittest.main()
