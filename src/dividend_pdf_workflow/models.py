from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ParsedPage:
    page_number: int
    text: str
    tables: list[list[list[str]]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParsedDocument:
    path: str
    filename: str
    company: str
    document_type: str
    reporting_period: str | None
    publication_date: str | None
    pages: list[ParsedPage] = field(default_factory=list)
    parse_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceItem:
    id: str
    company: str
    document: str
    document_type: str
    reporting_period: str | None
    dividend_period: str | None
    publication_date: str | None
    page: int
    kind: str
    value: float | None
    unit: str | None
    snippet: str
    confidence: str
    notes: str | None = None
    superseded_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RankingResult:
    selected_source: EvidenceItem | None
    superseded: list[EvidenceItem]
    manual_review: list[str]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Scenario:
    name: str
    estimate: str
    formula: str
    evidence_ids: list[str]
    missing_inputs: list[str]
    confidence: str
    flags: list[str] = field(default_factory=list)
    arithmetic: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReportModel:
    company: str
    documents: list[ParsedDocument]
    evidence: list[EvidenceItem]
    ranking: RankingResult
    scenarios: list[Scenario]
    manual_review_flags: list[str] = field(default_factory=list)
    rejected_claims: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
