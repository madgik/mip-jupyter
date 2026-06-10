import unittest

from mip import Report
from mip import ReportSection
from mip.results import ResultTable


class TestReport(unittest.TestCase):
    def test_report_construction(self):
        table = ResultTable.from_rows([{"a": 1}])
        report = Report(
            title="Analysis",
            sections=[ReportSection(title="Section", result=table)],
        )
        self.assertEqual(report.title, "Analysis")
        self.assertEqual(len(report.sections), 1)

    def test_display_fallback_prints(self):
        report = Report(
            title="Analysis",
            sections=[ReportSection(title="Section", result=ResultTable.from_rows([{"a": 1}]))],
        )
        report.display()


if __name__ == "__main__":
    unittest.main()
