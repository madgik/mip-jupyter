import unittest
from types import SimpleNamespace

from mip import AnalysisSet


class Var:
    def __init__(self, code):
        self.code = code


class TestAnalysisSet(unittest.TestCase):
    def test_inputdata_uses_new_shape(self):
        dm = SimpleNamespace(code="dementia", version="0.1")
        adni = SimpleNamespace(code="adni")
        age = Var("age")
        sex = Var("sex")
        analysis_set = AnalysisSet(data_model=dm, datasets=[adni], variables=[age, sex])

        payload = analysis_set.inputdata(filters={"condition": "AND", "rules": []})

        self.assertEqual(payload["data_model"], "dementia:0.1")
        self.assertEqual(payload["datasets"], ["adni"])
        self.assertEqual(payload["variables"], ["age", "sex"])
        self.assertIsNone(payload["validation_datasets"])
        self.assertNotIn("x", payload)
        self.assertNotIn("y", payload)


if __name__ == "__main__":
    unittest.main()
