---
name: dividend-evidence-extract
description: Extract dividend-relevant evidence from parsed PDF artifacts, including declared/proposed dividend per share, payout ratio, EPS, share price if present, and cited snippets.
---

# Dividend Evidence Extract

Use this skill after `dividend-pdf-ingest`.

## Input

- `<company-folder>/parsed-documents.json`

## Output

- `<company-folder>/evidence.json`

Every evidence item must include document, page, snippet, evidence kind, value/unit when numeric, reporting period, dividend period when known, and confidence.

## Automation

From the repo root, run:

```bash
PYTHONPATH=src python3 scripts/dividend_skill_step.py extract <company-folder>
```

## Extraction Rules

- Keep evidence citation-first; never create a value without a supporting page snippet.
- Extract share price only if it appears in the provided PDFs.
- Ignore total payout amounts such as `EUR 3.3 bn` when the task needs per-share dividend.
- Ignore additional-dividend mechanics unless they are explicitly the primary dividend claim.
- If wording is qualitative or ambiguous, keep it out of numeric estimates unless the Python extractor supports it.
