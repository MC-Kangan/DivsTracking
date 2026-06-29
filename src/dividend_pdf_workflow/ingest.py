from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from .models import ParsedDocument, ParsedPage


def ingest_company_folder(folder: Path) -> list[ParsedDocument]:
    documents: list[ParsedDocument] = []
    for pdf_path in sorted(folder.glob("*.pdf")):
        documents.append(ingest_pdf(pdf_path, company=folder.name))
    return documents


def ingest_pdf(pdf_path: Path, company: str) -> ParsedDocument:
    filename = pdf_path.name
    document = ParsedDocument(
        path=str(pdf_path),
        filename=filename,
        company=company,
        document_type=infer_document_type(filename),
        reporting_period=infer_reporting_period(filename),
        publication_date=infer_publication_date(filename),
    )
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            pages: list[ParsedPage] = []
            first_page_text = ""
            for index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if index == 1:
                    first_page_text = text
                tables = page.extract_tables() or []
                pages.append(ParsedPage(page_number=index, text=text, tables=tables))
            document.pages = pages
            if not document.reporting_period:
                document.reporting_period = infer_reporting_period(first_page_text)
            if not document.publication_date:
                document.publication_date = infer_publication_date(first_page_text)
    except Exception as exc:  # pragma: no cover - depends on external PDF parser failures.
        document.parse_error = str(exc)
    return document


def infer_document_type(text: str) -> str:
    value = text.lower()
    if "annual" in value or "group-report" in value:
        return "annual_report"
    if "quarter" in value or "q1" in value or "q2" in value or "q3" in value or "q4" in value or "interim" in value:
        return "quarterly_report"
    if "presentation" in value:
        return "investor_presentation"
    if "transcript" in value:
        return "transcript"
    if "fact-sheet" in value or "factsheet" in value:
        return "fact_sheet"
    return "unknown"


def infer_reporting_period(text: str) -> str | None:
    quarter = re.search(r"\bQ([1-4])[-_\s]*(20\d{2})\b", text, re.IGNORECASE)
    if quarter:
        return f"Q{quarter.group(1)} {quarter.group(2)}"
    annual = re.search(r"\b(?:FY|fiscal year|financial year|annual report|report)[-_\s]*(20\d{2})\b", text, re.IGNORECASE)
    if annual:
        return f"FY{annual.group(1)}"
    year = re.search(r"\b(20\d{2})\b", text)
    if year:
        return f"FY{year.group(1)}"
    return None


def infer_publication_date(text: str) -> str | None:
    quarter = re.search(r"\bQ([1-4])[-_\s]*(20\d{2})\b", text, re.IGNORECASE)
    if quarter:
        month_by_quarter = {"1": "05", "2": "08", "3": "11", "4": "02"}
        year = int(quarter.group(2))
        quarter_number = quarter.group(1)
        publication_year = year + 1 if quarter_number == "4" else year
        return f"{publication_year}-{month_by_quarter[quarter_number]}"
    year = re.search(r"\b(20\d{2})\b", text)
    if year:
        return f"{year.group(1)}-03"
    return None
