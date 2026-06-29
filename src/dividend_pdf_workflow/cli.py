from __future__ import annotations

import argparse
from pathlib import Path

from .extract import extract_evidence
from .ingest import ingest_company_folder
from .models import ParsedDocument, ReportModel
from .rank import rank_dividend_sources
from .reason import build_scenarios
from .report import render_html_report
from .validate import validate_report_model


def run_workflow(company_folder: Path, parsed_documents: list[ParsedDocument] | None = None) -> Path:
    company_folder = Path(company_folder)
    documents = parsed_documents if parsed_documents is not None else ingest_company_folder(company_folder)
    evidence = extract_evidence(documents)
    ranking = rank_dividend_sources(evidence, documents)
    scenarios = build_scenarios(evidence, ranking)
    report_model = ReportModel(
        company=company_folder.name,
        documents=documents,
        evidence=evidence,
        ranking=ranking,
        scenarios=scenarios,
    )
    validated = validate_report_model(report_model)
    output_path = company_folder / "dividend-report.html"
    output_path.write_text(render_html_report(validated), encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze company PDFs for dividend evidence.")
    parser.add_argument("company_folder", type=Path, help="Folder containing PDFs for one company.")
    args = parser.parse_args(argv)
    output_path = run_workflow(args.company_folder)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
