---
name: dividend-reasoning-branches
description: Build cited dividend estimate scenarios from ranked dividend evidence, including confirmed/minimum, base case, optimistic, and cannot-estimate branches.
---

# Dividend Reasoning Branches

Use this skill after `dividend-source-rank`.

## Inputs

- `<company-folder>/evidence.json`
- `<company-folder>/ranking.json`

## Output

- `<company-folder>/scenarios.json`

## Automation

From the repo root, run:

```bash
PYTHONPATH=src python3 scripts/dividend_skill_step.py reason <company-folder>
```

## Reasoning Rules

- Use only evidence IDs from `evidence.json`.
- Show formula, arithmetic, cited inputs, missing inputs, confidence, and flags.
- Produce a confirmed/minimum scenario from the latest clear dividend source.
- Add a base-case scenario only when cited EPS and cited payout ratio are available.
- Do not calculate dividend yield unless share price evidence exists in the PDFs.
- If inputs are missing, add missing-input flags rather than inventing assumptions.
