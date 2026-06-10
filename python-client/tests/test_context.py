import unittest

from mip import Context
from mip import FilterGroup
from mip import Rule
from mip.filters import Case
from mip.transformations import CategoricalFromFilters


class TestContext(unittest.TestCase):
    def test_context_is_immutable_and_serializable_fields(self):
        context = Context(
            data_model="stroke:1.0",
            datasets=["ssrdataset_harmonized"],
            mip_version="dev",
            filters=FilterGroup.and_(Rule("age", ">", 18)),
        )
        self.assertEqual(context.data_model, "stroke:1.0")
        self.assertEqual(context.datasets, ("ssrdataset_harmonized",))
        self.assertEqual(context.mip_version, "dev")
        self.assertIsNotNone(context.filters)

    def test_with_transformations_returns_new_context(self):
        context = Context(data_model="stroke:1.0", datasets=["ds1"])
        transformation = CategoricalFromFilters(
            name="cohort",
            label="Cohort",
            cases=[Case(label="A", when=FilterGroup.and_(Rule("x", "==", "1")))],
        )
        updated = context.with_transformations([transformation])
        self.assertEqual(len(updated.transformations), 1)
        self.assertEqual(len(context.transformations), 0)


if __name__ == "__main__":
    unittest.main()
