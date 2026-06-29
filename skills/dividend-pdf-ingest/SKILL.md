---
name: dividend-pdf-ingest
description: Extract text, tables, pages, document type, reporting period, and publication-date hints from one company folder of PDFs for the dividend PDF workflow.
---

# Dividend PDF Ingest

Use this skill as the first step of the dividend workflow when a company folder contains PDFs such as annual reports, quarterly reports, presentations, fact sheets, or transcripts.

## Input

- One company folder containing PDF files.

## Output

- `<company-folder>/parsed-documents.json`

Each parsed document preserves filename, inferred document type, reporting period, publication date, page numbers, page text, tables, and parse errors.

## Automation

From the repo root, run:

```bash
PYTHONPATH=src python3 scripts/dividend_skill_step.py ingest <company-folder>
```

## Failure Handling

- If one PDF cannot be parsed, keep the parse error in the JSON and continue.
- Do not manually infer missing metadata unless the source filename or page text supports it.
- Do not delete or modify source PDFs.
