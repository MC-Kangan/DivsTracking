---
name: dividend-pdf-workflow
description: Run the full document-only dividend analysis workflow for one company folder of PDF reports, producing cited JSON artifacts and dividend-report.html with latest-source ranking, scenario estimates, manual-review flags, and no external market data.
---

# Dividend PDF Workflow

Use this skill when the user asks to analyze company reports for dividend payment, payout policy, dividend estimates, or dividend evidence from PDFs.

## Rules

- Analyze one company folder at a time.
- Use only PDFs and artifacts in the provided folder.
- Do not fetch share prices, forecasts, exchange rates, or market data.
- Every estimate must trace to evidence in the generated artifacts.
- If required information is missing or ambiguous, preserve a manual-review flag.
- Prefer the latest clear dividend source. A newer report with no dividend statement does not invalidate an older clear source.

## Automation

From the repo root, run:

```bash
PYTHONPATH=src python3 scripts/dividend_skill_step.py all <company-folder>
```

This writes:

- `<company-folder>/parsed-documents.json`
- `<company-folder>/evidence.json`
- `<company-folder>/ranking.json`
- `<company-folder>/scenarios.json`
- `<company-folder>/report-model.json`
- `<company-folder>/dividend-report.html`

## Step Order

If running manually or debugging, use these skills in order:

1. `dividend-pdf-ingest`
2. `dividend-evidence-extract`
3. `dividend-source-rank`
4. `dividend-reasoning-branches`
5. `dividend-report-render`

## Final Checks

Run tests after code changes:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Open or inspect `dividend-report.html`. Confirm it includes Executive Summary, Latest Dividend Source, Evidence Table, Manual Review, Reasoning Tree, and Superseded Evidence.
