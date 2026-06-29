---
name: dividend-source-rank
description: Rank dividend evidence to choose the latest clear dividend source, detect newer silent reports, and mark older conflicting evidence as superseded.
---

# Dividend Source Rank

Use this skill after `dividend-evidence-extract`.

## Inputs

- `<company-folder>/parsed-documents.json`
- `<company-folder>/evidence.json`

## Output

- `<company-folder>/ranking.json`

## Automation

From the repo root, run:

```bash
PYTHONPATH=src python3 scripts/dividend_skill_step.py rank <company-folder>
```

## Ranking Rules

- Prefer evidence from the latest relevant dividend period.
- Use reporting period and publication date for recency, but do not treat a newer silent report as a newer dividend statement.
- Within the same dividend period, prefer formal sources over less formal sources.
- If Q1 2026 has no dividend statement but FY2025 annual report has one, select the FY2025 annual report.
- If Q4 2025 and Q2 2025 conflict for the same dividend period, select Q4 2025 and mark Q2 superseded.
- If dates or periods are ambiguous, preserve manual-review flags rather than guessing.
