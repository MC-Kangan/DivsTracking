from __future__ import annotations

import re

from .models import EvidenceItem, ParsedDocument


DIVIDEND_AMOUNT_PATTERNS = [
    re.compile(
        r"(?:dividend|distribution)[^.]{0,100}?(?:EUR|€)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:per share|/share|per no-par-value share)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:EUR|€)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:per share|/share|per no-par-value share)[^.]{0,80}?(?:dividend|distribution)",
        re.IGNORECASE,
    ),
    re.compile(
        r"dividend\s+per\s+(?:ordinary|preferred|no-par-value)?\s*share[^€EUR]{0,40}(?:EUR|€)\s*([0-9]+(?:\.[0-9]+)?)",
        re.IGNORECASE,
    ),
]
PAYOUT_RATIO_PATTERN = re.compile(r"(?:dividend\s+)?payout ratio[^0-9%]{0,40}([0-9]+(?:\.[0-9]+)?)\s*%", re.IGNORECASE)
EPS_PATTERNS = [
    re.compile(
        r"(?:earnings per share|EPS)[^.]{0,80}?(?:amounted to|was|were|=|:)\s*(?:EUR|€)\s*([0-9]+(?:\.[0-9]+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:earnings per share|EPS)\s*\(?(?:in\s+)?(?:euros|eur)\)?[^0-9]{0,40}([0-9]+(?:\.[0-9]+)?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:basic/diluted|basic|diluted) earnings per (?:ordinary|preferred)?\s*share\s*(?:EUR|€)\s*([0-9]+(?:\.[0-9]+)?)",
        re.IGNORECASE,
    ),
]
SHARE_PRICE_PATTERN = re.compile(r"(?:share price|stock price)[^0-9€EUR-]{0,40}(?:EUR|€)?\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)


def extract_evidence(documents: list[ParsedDocument]) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for doc in documents:
        if doc.parse_error:
            continue
        for page in doc.pages:
            text = _normalize(page.text)
            evidence.extend(_extract_dividend_amounts(doc, page.page_number, text))
            evidence.extend(_extract_simple_metric(doc, page.page_number, text, PAYOUT_RATIO_PATTERN, "dividend_payout_ratio", "%"))
            for eps_pattern in EPS_PATTERNS:
                evidence.extend(_extract_simple_metric(doc, page.page_number, text, eps_pattern, "earnings_per_share", "EUR/share"))
            evidence.extend(_extract_simple_metric(doc, page.page_number, text, SHARE_PRICE_PATTERN, "share_price", "EUR"))
    return evidence


def _extract_dividend_amounts(doc: ParsedDocument, page_number: int, text: str) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for pattern in DIVIDEND_AMOUNT_PATTERNS:
        for match in pattern.finditer(text):
            value = float(match.group(1))
            snippet = _snippet(text, match.start(), match.end())
            if _is_non_primary_dividend_snippet(snippet):
                continue
            kind = "proposed_dividend_per_share" if re.search(r"propos", snippet, re.IGNORECASE) else "declared_dividend_per_share"
            items.append(
                EvidenceItem(
                    id=_evidence_id(doc, page_number, kind, len(items) + 1),
                    company=doc.company,
                    document=doc.filename,
                    document_type=doc.document_type,
                    reporting_period=doc.reporting_period,
                    dividend_period=_infer_dividend_period(text, doc.reporting_period),
                    publication_date=doc.publication_date,
                    page=page_number,
                    kind=kind,
                    value=value,
                    unit="EUR/share",
                    snippet=snippet,
                    confidence="high",
                )
            )
    return _dedupe(items)


def _extract_simple_metric(
    doc: ParsedDocument,
    page_number: int,
    text: str,
    pattern: re.Pattern[str],
    kind: str,
    unit: str,
) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for index, match in enumerate(pattern.finditer(text), start=1):
        items.append(
            EvidenceItem(
                id=_evidence_id(doc, page_number, kind, index),
                company=doc.company,
                document=doc.filename,
                document_type=doc.document_type,
                reporting_period=doc.reporting_period,
                dividend_period=_infer_dividend_period(text, doc.reporting_period) if "dividend" in kind else None,
                publication_date=doc.publication_date,
                page=page_number,
                kind=kind,
                value=float(match.group(1)),
                unit=unit,
                snippet=_snippet(text, match.start(), match.end()),
                confidence="medium" if kind == "share_price" else "high",
            )
        )
    return items


def _infer_dividend_period(text: str, fallback: str | None) -> str | None:
    fiscal_match = re.search(r"(?:fiscal year|financial year|FY)\s*(20\d{2})", text, re.IGNORECASE)
    if fiscal_match:
        return f"FY{fiscal_match.group(1)}"
    return fallback


def _evidence_id(doc: ParsedDocument, page_number: int, kind: str, index: int) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", doc.filename.lower()).strip("-")
    return f"{stem}-p{page_number}-{kind}-{index}"


def _snippet(text: str, start: int, end: int) -> str:
    return text[max(0, start - 90) : min(len(text), end + 90)].strip()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or " ").strip()


def _is_non_primary_dividend_snippet(snippet: str) -> bool:
    lowered = snippet.lower()
    if "additional dividend" in lowered or "ditional dividend" in lowered:
        return True
    if re.search(r"\b(bn|billion|million|€\s*million|eur\s*million)\b", lowered) and not re.search(
        r"per (?:ordinary |preferred |no-par-value )?share", lowered
    ):
        return True
    return False


def _dedupe(items: list[EvidenceItem]) -> list[EvidenceItem]:
    seen: set[tuple[str, float | None, int]] = set()
    unique: list[EvidenceItem] = []
    for item in items:
        key = (item.kind, item.value, item.page)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique
