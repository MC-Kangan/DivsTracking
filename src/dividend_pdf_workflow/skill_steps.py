from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .extract import extract_evidence
from .ingest import ingest_company_folder
from .models import EvidenceItem, ParsedDocument, ParsedPage, RankingResult, ReportModel, Scenario
from .rank import rank_dividend_sources
from .reason import build_scenarios
from .report import render_html_report
from .validate import validate_report_model


PARSED_FILE = "parsed-documents.json"
EVIDENCE_FILE = "evidence.json"
RANKING_FILE = "ranking.json"
SCENARIOS_FILE = "scenarios.json"
REPORT_MODEL_FILE = "report-model.json"


def run_step(step: str, company_folder: Path) -> Path:
    company_folder = Path(company_folder)
    if step == "ingest":
        documents = ingest_company_folder(company_folder)
        return _write_json(company_folder / PARSED_FILE, [doc.to_dict() for doc in documents])
    if step == "extract":
        documents = _read_documents(company_folder / PARSED_FILE)
        evidence = extract_evidence(documents)
        return _write_json(company_folder / EVIDENCE_FILE, [item.to_dict() for item in evidence])
    if step == "rank":
        documents = _read_documents(company_folder / PARSED_FILE)
        evidence = _read_evidence(company_folder / EVIDENCE_FILE)
        ranking = rank_dividend_sources(evidence, documents)
        return _write_json(company_folder / RANKING_FILE, ranking.to_dict())
    if step == "reason":
        evidence = _read_evidence(company_folder / EVIDENCE_FILE)
        ranking = _read_ranking(company_folder / RANKING_FILE)
        scenarios = build_scenarios(evidence, ranking)
        return _write_json(company_folder / SCENARIOS_FILE, [scenario.to_dict() for scenario in scenarios])
    if step == "validate":
        documents = _read_documents(company_folder / PARSED_FILE)
        evidence = _read_evidence(company_folder / EVIDENCE_FILE)
        ranking = _read_ranking(company_folder / RANKING_FILE)
        scenarios = _read_scenarios(company_folder / SCENARIOS_FILE)
        report = ReportModel(
            company=company_folder.name,
            documents=documents,
            evidence=evidence,
            ranking=ranking,
            scenarios=scenarios,
        )
        validated = validate_report_model(report)
        return _write_json(company_folder / REPORT_MODEL_FILE, validated.to_dict())
    if step == "render":
        report = _read_report_model(company_folder / REPORT_MODEL_FILE)
        output = company_folder / "dividend-report.html"
        output.write_text(render_html_report(report), encoding="utf-8")
        return output
    if step == "all":
        for item in ["ingest", "extract", "rank", "reason", "validate", "render"]:
            output = run_step(item, company_folder)
        return output
    raise ValueError(f"Unknown step: {step}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one dividend PDF workflow skill step.")
    parser.add_argument(
        "step",
        choices=["ingest", "extract", "rank", "reason", "validate", "render", "all"],
        help="Workflow step to run.",
    )
    parser.add_argument("company_folder", type=Path, help="Company folder or artifact folder.")
    args = parser.parse_args(argv)
    output = run_step(args.step, args.company_folder)
    print(f"Wrote {output}")
    return 0


def _write_json(path: Path, data: Any) -> Path:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_documents(path: Path) -> list[ParsedDocument]:
    return [_document_from_dict(item) for item in _read_json(path)]


def _document_from_dict(data: dict[str, Any]) -> ParsedDocument:
    pages = [ParsedPage(**page) for page in data.get("pages", [])]
    return ParsedDocument(
        path=data["path"],
        filename=data["filename"],
        company=data["company"],
        document_type=data["document_type"],
        reporting_period=data.get("reporting_period"),
        publication_date=data.get("publication_date"),
        pages=pages,
        parse_error=data.get("parse_error"),
    )


def _read_evidence(path: Path) -> list[EvidenceItem]:
    return [EvidenceItem(**item) for item in _read_json(path)]


def _read_ranking(path: Path) -> RankingResult:
    data = _read_json(path)
    selected = data.get("selected_source")
    return RankingResult(
        selected_source=EvidenceItem(**selected) if selected else None,
        superseded=[EvidenceItem(**item) for item in data.get("superseded", [])],
        manual_review=data.get("manual_review", []),
        explanation=data.get("explanation", ""),
    )


def _read_scenarios(path: Path) -> list[Scenario]:
    return [Scenario(**item) for item in _read_json(path)]


def _read_report_model(path: Path) -> ReportModel:
    data = _read_json(path)
    return ReportModel(
        company=data["company"],
        documents=[_document_from_dict(item) for item in data.get("documents", [])],
        evidence=[EvidenceItem(**item) for item in data.get("evidence", [])],
        ranking=_ranking_from_data(data["ranking"]),
        scenarios=[Scenario(**item) for item in data.get("scenarios", [])],
        manual_review_flags=data.get("manual_review_flags", []),
        rejected_claims=data.get("rejected_claims", []),
    )


def _ranking_from_data(data: dict[str, Any]) -> RankingResult:
    selected = data.get("selected_source")
    return RankingResult(
        selected_source=EvidenceItem(**selected) if selected else None,
        superseded=[EvidenceItem(**item) for item in data.get("superseded", [])],
        manual_review=data.get("manual_review", []),
        explanation=data.get("explanation", ""),
    )


if __name__ == "__main__":
    raise SystemExit(main())
