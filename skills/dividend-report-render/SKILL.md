---
name: dividend-report-render
description: Validate dividend workflow artifacts and render the final standalone dividend-report.html with citations, scenarios, manual-review flags, reasoning tree, and superseded evidence.
---

# Dividend Report Render

Use this skill after `dividend-reasoning-branches`.

## Inputs

- `<company-folder>/parsed-documents.json`
- `<company-folder>/evidence.json`
- `<company-folder>/ranking.json`
- `<company-folder>/scenarios.json`

## Outputs

- `<company-folder>/report-model.json`
- `<company-folder>/dividend-report.html`

## Automation

From the repo root, run:

```bash
PYTHONPATH=src python3 scripts/dividend_skill_step.py validate <company-folder>
PYTHONPATH=src python3 scripts/dividend_skill_step.py render <company-folder>
```

## Report Requirements

The HTML report must include:

- Executive Summary
- Scenario Estimates
- Latest Dividend Source
- Evidence Table
- Manual Review
- Reasoning Tree
- Superseded Evidence
- Unavailable Or Failed PDF Parsing

Validation must reject unsupported evidence IDs and preserve missing external data flags, especially missing share price for dividend yield.
