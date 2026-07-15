import unittest

from mip.catalog_registry import (
    PIPELINE_BACKEND_ALGORITHMS,
    validate_client_registry,
)
from mip.preprocessing import PREPROCESSING_STEP_CLASSES, PREPROCESSING_STEP_NAMES


class TestCatalogRegistry(unittest.TestCase):
    def test_validate_client_registry_passes(self):
        validate_client_registry()

    def test_pipeline_registry_has_unique_backend_mappings(self):
        self.assertEqual(len(PIPELINE_BACKEND_ALGORITHMS), len(set(PIPELINE_BACKEND_ALGORITHMS.values())))

    def test_preprocessing_registry_covers_four_steps(self):
        self.assertEqual(len(PREPROCESSING_STEP_CLASSES), 4)
        self.assertEqual(len(PREPROCESSING_STEP_NAMES), 4)
        self.assertEqual(
            set(PREPROCESSING_STEP_NAMES),
            {cls.name for cls in PREPROCESSING_STEP_CLASSES},
        )


if __name__ == "__main__":
    unittest.main()
