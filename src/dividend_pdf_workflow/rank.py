from __future__ import annotations

import re

from .models import EvidenceItem, ParsedDocument, RankingResult


DOCUMENT_TYPE_PRIORITY = {
    "annual_report": 5,
    "audited_report": 5,
    "quarterly_report": 4,
    "interim_report": 4,
    "investor_presentation": 3,
    "presentation": 3,
    "transcript": 2,
    "fact_sheet": 1,
    "unknown": 0,
}


DIVIDEND_KINDS = {
    "declared_dividend_per_share",
    "proposed_dividend_per_share",
    "paid_dividend_per_share",
    "dividend_per_share",
}


def rank_dividend_sources(
    evidence: list[EvidenceItem],
    documents: list[ParsedDocument],
) -> RankingResult:
    dividend_evidence = [
        item
        for item in evidence
        if item.kind in DIVIDEND_KINDS and item.value is not None
    ]

    manual_review: list[str] = []
    for item in dividend_evidence:
        if not item.dividend_period or not item.reporting_period:
            manual_review.append(f"Ambiguous period for evidence {item.id}.")

    if not dividend_evidence:
        return RankingResult(
            selected_source=None,
            superseded=[],
            manual_review=manual_review,
            explanation="No clear dividend source found in provided documents.",
        )

    sorted_evidence = sorted(dividend_evidence, key=_evidence_sort_key, reverse=True)
    selected = sorted_evidence[0]
    superseded: list[EvidenceItem] = []
    for item in sorted_evidence[1:]:
        if item.dividend_period == selected.dividend_period and item.value != selected.value:
            item.superseded_by = selected.id
            superseded.append(item)

    silent_newer_docs = [
        doc.filename
        for doc in documents
        if _doc_sort_key(doc) > _evidence_doc_sort_key(selected)
        and not _document_has_dividend_evidence(doc, dividend_evidence)
    ]

    explanation_parts = [
        f"Selected {selected.document} page {selected.page} as the latest clear dividend source."
    ]
    for filename in silent_newer_docs:
        explanation_parts.append(
            f"{filename} contained no clear dividend statement and did not invalidate the selected source."
        )
    for item in superseded:
        explanation_parts.append(f"{item.id} was superseded by {selected.id}.")

    return RankingResult(
        selected_source=selected,
        superseded=superseded,
        manual_review=manual_review,
        explanation=" ".join(explanation_parts),
    )


def _document_has_dividend_evidence(doc: ParsedDocument, evidence: list[EvidenceItem]) -> bool:
    return any(item.document == doc.filename for item in evidence)


def _evidence_sort_key(item: EvidenceItem) -> tuple[int, str, int, str]:
    return (
        _period_score(item.dividend_period or item.reporting_period),
        item.publication_date or "",
        DOCUMENT_TYPE_PRIORITY.get(item.document_type, 0),
        item.id,
    )


def _evidence_doc_sort_key(item: EvidenceItem) -> tuple[int, str, int, str]:
    return (
        _period_score(item.reporting_period or item.dividend_period),
        item.publication_date or "",
        DOCUMENT_TYPE_PRIORITY.get(item.document_type, 0),
        item.document,
    )


def _doc_sort_key(doc: ParsedDocument) -> tuple[int, str, int, str]:
    return (
        _period_score(doc.reporting_period),
        doc.publication_date or "",
        DOCUMENT_TYPE_PRIORITY.get(doc.document_type, 0),
        doc.filename,
    )


def _period_score(period: str | None) -> int:
    if not period:
        return 0
    match = re.search(r"(20\d{2})", period)
    if not match:
        return 0
    year = int(match.group(1))
    quarter_match = re.search(r"\bQ([1-4])\b", period.upper())
    quarter = int(quarter_match.group(1)) if quarter_match else 5
    return year * 10 + quarter
