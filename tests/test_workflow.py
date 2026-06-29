import tempfile
import unittest
from pathlib import Path

from dividend_pdf_workflow.models import EvidenceItem, ParsedDocument, ParsedPage, RankingResult, ReportModel, Scenario


def make_document(
    filename,
    document_type,
    reporting_period,
    publication_date,
):
    return ParsedDocument(
        path=filename,
        filename=filename,
        company="TEST",
        document_type=document_type,
        reporting_period=reporting_period,
        publication_date=publication_date,
    )


def make_evidence(
    evidence_id,
    document,
    document_type,
    reporting_period,
    dividend_period,
    publication_date,
    value,
    kind="declared_dividend_per_share",
):
    return EvidenceItem(
        id=evidence_id,
        company="TEST",
        document=document,
        document_type=document_type,
        reporting_period=reporting_period,
        dividend_period=dividend_period,
        publication_date=publication_date,
        page=5,
        kind=kind,
        value=value,
        unit="EUR/share" if value is not None else None,
        snippet=f"Dividend {value}",
        confidence="high",
    )


class WorkflowTests(unittest.TestCase):
    def test_evidence_item_serializes_with_dividend_period(self):
        from dividend_pdf_workflow.models import EvidenceItem

        item = EvidenceItem(
            id="BMW-annual-2025-p10-dividend",
            company="BMW",
            document="annual.pdf",
            document_type="annual_report",
            reporting_period="FY2025",
            dividend_period="FY2025",
            publication_date="2026-03",
            page=10,
            kind="declared_dividend_per_share",
            value=4.30,
            unit="EUR/share",
            snippet="Dividend proposed: EUR 4.30 per share.",
            confidence="high",
        )

        self.assertEqual(item.to_dict()["dividend_period"], "FY2025")
        self.assertEqual(item.to_dict()["value"], 4.30)

    def test_deterministic_adapter_returns_schema_safe_empty_result(self):
        from dividend_pdf_workflow.llm import DeterministicLLMAdapter

        adapter = DeterministicLLMAdapter()

        self.assertEqual(adapter.generate_structured("prompt", {"type": "object"}, {}), {})

    def test_newer_silent_document_does_not_invalidate_latest_clear_source(self):
        from dividend_pdf_workflow.rank import rank_dividend_sources

        documents = [
            make_document("q1-2026.pdf", "quarterly_report", "Q1 2026", "2026-05"),
            make_document("annual-2025.pdf", "annual_report", "FY2025", "2026-03"),
        ]
        evidence = [
            make_evidence(
                "annual-2025-dividend",
                "annual-2025.pdf",
                "annual_report",
                "FY2025",
                "FY2025",
                "2026-03",
                4.30,
            )
        ]

        result = rank_dividend_sources(evidence, documents)

        self.assertEqual(result.selected_source.id, "annual-2025-dividend")
        self.assertIn("q1-2026.pdf contained no clear dividend statement", result.explanation)

    def test_newer_clear_source_supersedes_older_conflicting_source(self):
        from dividend_pdf_workflow.rank import rank_dividend_sources

        documents = [
            make_document("q4-2025.pdf", "quarterly_report", "Q4 2025", "2026-02"),
            make_document("q2-2025.pdf", "quarterly_report", "Q2 2025", "2025-08"),
        ]
        evidence = [
            make_evidence("q2-dividend", "q2-2025.pdf", "quarterly_report", "Q2 2025", "FY2025", "2025-08", 3.80),
            make_evidence("q4-dividend", "q4-2025.pdf", "quarterly_report", "Q4 2025", "FY2025", "2026-02", 4.10),
        ]

        result = rank_dividend_sources(evidence, documents)

        self.assertEqual(result.selected_source.id, "q4-dividend")
        self.assertEqual([item.id for item in result.superseded], ["q2-dividend"])
        self.assertEqual(result.superseded[0].superseded_by, "q4-dividend")

    def test_validation_rejects_scenario_with_missing_evidence_id(self):
        from dividend_pdf_workflow.validate import validate_report_model

        evidence = [
            make_evidence("known", "annual-2025.pdf", "annual_report", "FY2025", "FY2025", "2026-03", 4.30)
        ]
        report = ReportModel(
            company="TEST",
            documents=[],
            evidence=evidence,
            ranking=RankingResult(evidence[0], [], [], "Selected annual report."),
            scenarios=[
                Scenario(
                    name="base case",
                    estimate="EUR 4.30/share",
                    formula="declared dividend",
                    evidence_ids=["missing"],
                    missing_inputs=[],
                    confidence="low",
                )
            ],
        )

        validated = validate_report_model(report)

        self.assertIn("missing evidence id: missing", validated.rejected_claims)
        self.assertIn("Missing external data: share price not found in provided PDFs; dividend yield not calculated.", validated.manual_review_flags)

    def test_extracts_dividend_amount_with_page_citation(self):
        from dividend_pdf_workflow.extract import extract_evidence

        doc = make_document("annual-2025.pdf", "annual_report", "FY2025", "2026-03")
        doc.pages = [
            ParsedPage(
                page_number=42,
                text="The Board proposes a dividend of EUR 4.30 per share for fiscal year 2025.",
            )
        ]

        evidence = extract_evidence([doc])

        dividend_items = [item for item in evidence if item.kind == "proposed_dividend_per_share"]
        self.assertEqual(len(dividend_items), 1)
        self.assertEqual(dividend_items[0].value, 4.30)
        self.assertEqual(dividend_items[0].page, 42)
        self.assertEqual(dividend_items[0].dividend_period, "FY2025")

    def test_extracts_payout_ratio_and_eps(self):
        from dividend_pdf_workflow.extract import extract_evidence

        doc = make_document("annual-2025.pdf", "annual_report", "FY2025", "2026-03")
        doc.pages = [
            ParsedPage(
                page_number=9,
                text="Dividend payout ratio was 40%. Earnings per share amounted to EUR 10.00.",
            )
        ]

        evidence = extract_evidence([doc])

        kinds = {item.kind: item.value for item in evidence}
        self.assertEqual(kinds["dividend_payout_ratio"], 40.0)
        self.assertEqual(kinds["earnings_per_share"], 10.0)

    def test_eps_extraction_ignores_unrelated_numbers_after_heading(self):
        from dividend_pdf_workflow.extract import extract_evidence

        doc = make_document("annual-2025.pdf", "annual_report", "FY2025", "2026-03")
        doc.pages = [
            ParsedPage(
                page_number=283,
                text="Earnings per share are calculated as follows: payments are due within 30 days.",
            )
        ]

        evidence = extract_evidence([doc])

        self.assertNotIn("earnings_per_share", {item.kind for item in evidence})

    def test_extraction_ignores_total_payout_and_additional_dividend(self):
        from dividend_pdf_workflow.extract import extract_evidence

        doc = make_document("q1-2026.pdf", "quarterly_report", "Q1 2026", "2026-05")
        doc.pages = [
            ParsedPage(
                page_number=4,
                text=(
                    "Prior to dividend payout of EUR 3.3 bn in April 2026. "
                    "Earnings to cover the additional dividend of EUR 0.02 per share."
                ),
            )
        ]

        evidence = extract_evidence([doc])

        self.assertEqual([item for item in evidence if "dividend" in item.kind], [])

    def test_extraction_accepts_no_par_value_share_dividend(self):
        from dividend_pdf_workflow.extract import extract_evidence

        doc = make_document("annual-2025.pdf", "annual_report", "FY2025", "2026-03")
        doc.pages = [
            ParsedPage(
                page_number=85,
                text="The Board will propose the payment of a dividend of EUR 3.50 per no-par-value share entitled to a dividend for the year 2025.",
            )
        ]

        evidence = extract_evidence([doc])

        dividend_items = [item for item in evidence if item.kind == "proposed_dividend_per_share"]
        self.assertEqual(len(dividend_items), 1)
        self.assertEqual(dividend_items[0].value, 3.50)

    def test_reasoning_builds_confirmed_scenario_and_flags_missing_yield(self):
        from dividend_pdf_workflow.reason import build_scenarios

        selected = make_evidence(
            "annual-2025-dividend",
            "annual-2025.pdf",
            "annual_report",
            "FY2025",
            "FY2025",
            "2026-03",
            4.30,
            kind="proposed_dividend_per_share",
        )
        ranking = RankingResult(selected, [], [], "Selected annual report.")

        scenarios = build_scenarios([selected], ranking)

        self.assertEqual(scenarios[0].name, "confirmed/minimum")
        self.assertEqual(scenarios[0].estimate, "EUR 4.30/share")
        self.assertEqual(scenarios[0].evidence_ids, ["annual-2025-dividend"])
        self.assertIn("share price", scenarios[0].missing_inputs)

    def test_html_report_contains_required_sections(self):
        from dividend_pdf_workflow.report import render_html_report

        selected = make_evidence(
            "annual-2025-dividend",
            "annual-2025.pdf",
            "annual_report",
            "FY2025",
            "FY2025",
            "2026-03",
            4.30,
            kind="proposed_dividend_per_share",
        )
        report = ReportModel(
            company="TEST",
            documents=[],
            evidence=[selected],
            ranking=RankingResult(selected, [], [], "Selected annual report."),
            scenarios=[
                Scenario(
                    name="confirmed/minimum",
                    estimate="EUR 4.30/share",
                    formula="latest clear dividend per share",
                    evidence_ids=[selected.id],
                    missing_inputs=["share price"],
                    confidence="high",
                )
            ],
            manual_review_flags=["Missing external data: share price not found in provided PDFs; dividend yield not calculated."],
        )

        html = render_html_report(report)

        self.assertIn("Executive Summary", html)
        self.assertIn("Latest Dividend Source", html)
        self.assertIn("Evidence Table", html)
        self.assertIn("Manual Review", html)
        self.assertIn("Reasoning Tree", html)
        self.assertIn("Superseded Evidence", html)

    def test_run_workflow_writes_report_for_folder(self):
        from dividend_pdf_workflow.cli import run_workflow

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            report_path = run_workflow(folder, parsed_documents=[
                ParsedDocument(
                    path="annual-2025.pdf",
                    filename="annual-2025.pdf",
                    company=folder.name,
                    document_type="annual_report",
                    reporting_period="FY2025",
                    publication_date="2026-03",
                    pages=[
                        ParsedPage(
                            page_number=1,
                            text="The Board proposes a dividend of EUR 4.30 per share for fiscal year 2025.",
                        )
                    ],
                )
            ])

            self.assertEqual(report_path, folder / "dividend-report.html")
            self.assertTrue(report_path.exists())
            self.assertIn("EUR 4.30/share", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
