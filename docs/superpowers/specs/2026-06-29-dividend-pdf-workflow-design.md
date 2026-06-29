# Dividend PDF Workflow Design

## Goal

Build a command-line workflow that analyzes a single company folder of PDF reports and produces an HTML report focused on dividends. The workflow must work from the supplied documents only, cite every source it uses, flag missing external data, and avoid unsupported assumptions.

The first target workspace contains company folders such as `BMW/` and `MBG/`, each holding annual reports, quarterly reports, investor presentations, and related PDFs.

## Scope

Included:

- Analyze one company folder at a time.
- Extract dividend-related evidence from all PDFs in that folder.
- Identify the latest clear dividend source even when the newest document has no dividend information.
- Mark older conflicting dividend evidence as superseded when a newer clear source exists.
- Estimate dividend payment scenarios only from cited document evidence.
- Generate `dividend-report.html` inside the company folder.
- Preserve portability across different LLM models and agent frameworks.

Excluded from the first version:

- Fetching share prices, analyst estimates, exchange rates, or market data from the web.
- Calculating dividend yield unless share price evidence appears in the supplied PDFs.
- Combining multiple company folders into one run.
- Building an interactive web app.

## Architecture

The workflow uses deterministic extraction and validation around model-assisted reasoning:

```text
company folder
  -> PDF ingestion
  -> evidence registry
  -> dividend source ranking
  -> reasoning branches
  -> validation
  -> HTML report
```

The workflow is divided into skills with structured input and output contracts:

1. PDF Ingestion Skill
2. Evidence Extraction Skill
3. Dividend Source Ranking Skill
4. Reasoning Branch Skill
5. Validation Skill
6. HTML Report Skill

LLM-dependent work is accessed through an adapter interface. The core workflow owns the evidence schema, ranking rules, validation rules, and report schema so the system can run with different model providers or agent frameworks.

## Model And Agent Portability

The workflow must not depend on a single model SDK or agent framework. LLM calls use an `LLMAdapter` interface:

```text
LLMAdapter.generate_structured(prompt, schema, context) -> structured result
```

Adapters can be implemented for OpenAI, Anthropic, Gemini, local models, LangChain, LlamaIndex, Semantic Kernel, or a custom runner. The workflow should treat all adapters as untrusted producers of candidate structured output. Validation remains deterministic and rejects unsupported claims regardless of model.

The portable contract is:

- Inputs are plain JSON-compatible data structures.
- Outputs are schema-validated JSON-compatible data structures.
- Every generated claim that affects the report must reference evidence IDs.
- The model may propose reasoning branches, but it may not introduce new facts.
- Agent frameworks may orchestrate steps, but each skill contract remains stable.

## Skill Responsibilities

### PDF Ingestion Skill

Input:

- Path to one company folder.

Output:

- List of parsed documents with text blocks, tables, page numbers, filename, inferred document type, inferred reporting period, and inferred publication date when available.

Responsibilities:

- Extract text and tables from each PDF.
- Preserve page numbers for citations.
- Infer document type such as annual report, quarterly report, presentation, transcript, or fact sheet.
- Infer reporting period and publication date from filename, title page, headers, or document text.
- Flag parsing failures without stopping the whole workflow.

### Evidence Extraction Skill

Input:

- Parsed documents from PDF ingestion.

Output:

- Evidence registry containing dividend-relevant facts.

Evidence types include:

- Declared dividend per share.
- Proposed dividend per share.
- Paid dividend.
- Dividend payout ratio.
- Dividend policy.
- Earnings per share.
- Net profit or net income.
- Free cash flow.
- Share count.
- Prior-year dividend.
- Management guidance.
- Statements that no dividend was proposed or declared.
- Share price only if it appears in the provided PDFs.

Every extracted fact must include:

- Stable evidence ID.
- Company.
- Source document filename.
- Document type.
- Reporting period.
- Dividend period when the evidence refers to a specific dividend year or payment period.
- Publication date if known.
- Page number.
- Evidence kind.
- Value and unit when numeric.
- Exact or near-exact supporting snippet.
- Confidence.
- Extraction notes if ambiguous.

Example:

```json
{
  "id": "MBG-annual-2025-p142-dividend-proposal",
  "company": "MBG",
  "document": "mercedes-benz-annual-report-2025.pdf",
  "document_type": "annual_report",
  "reporting_period": "FY2025",
  "dividend_period": "FY2025",
  "publication_date": "2026-03",
  "page": 142,
  "kind": "declared_dividend_per_share",
  "value": 4.3,
  "unit": "EUR/share",
  "snippet": "supporting text from the page",
  "confidence": "high"
}
```

### Dividend Source Ranking Skill

Input:

- Evidence registry.
- Parsed document metadata.

Output:

- Selected latest clear dividend source.
- Superseded evidence list.
- Uncertain or manually reviewable evidence list.

Ranking rules:

1. Prefer dividend evidence from the latest relevant dividend period. Use reporting period and publication date to resolve recency, but do not confuse a newer report that is silent on dividends with a newer dividend statement.
2. Within the same dividend period, prefer formal sources over less formal sources: annual report or audited report, then quarterly report, then investor presentation, then transcript, then fact sheet.
3. If a newer document has no dividend evidence, do not treat that absence as a contradiction. Search backward to the latest clear dividend source.
4. If a newer document contains a different clear dividend statement for the same dividend period, mark the older statement as superseded.
5. If Q1 2026 has no dividend information but the FY2025 annual report has a clear dividend proposal, the FY2025 annual report is the latest clear source.
6. If Q4 2025 has a dividend statement and Q2 2025 has a different older dividend statement, Q4 2025 supersedes Q2 2025 for the same relevant dividend period.
7. If dates or reporting periods cannot be parsed reliably, flag the affected evidence for manual review instead of silently choosing.
8. If all available dividend evidence is stale, ambiguous, or unrelated to the target period, report that no estimate can be made from provided documents.

The ranking step must explain why the selected source was chosen and why superseded sources were ignored.

### Reasoning Branch Skill

Input:

- Evidence registry.
- Dividend source ranking output.

Output:

- Scenario branches with cited assumptions, formulas, arithmetic, confidence, and manual-review flags.

Branches:

- Confirmed/minimum scenario.
- Base-case scenario.
- Optimistic scenario.
- Cannot-estimate branch when needed.

Rules:

- Branches may use only evidence IDs from the registry.
- Branches must cite every numeric input.
- Branches must show formulas and arithmetic.
- Branches must identify missing inputs.
- Branches must not calculate dividend yield unless share price evidence appears in the PDFs.
- Branches must not use web or market data in the first version.

Example reasoning path:

1. Identify a cited payout ratio from a report.
2. Identify cited EPS or earnings from provided documents.
3. If only Q1 earnings are available, treat Q1 achieved earnings as a floor, not a full-year projection unless a cited full-year guidance exists.
4. Build scenarios from cited full-year guidance, historical annual evidence, or explicitly bounded partial-year evidence.
5. Flag missing forecast inputs instead of inventing them.

### Validation Skill

Input:

- Evidence registry.
- Ranking output.
- Reasoning branches.

Output:

- Validated report model.
- Rejected claims and manual-review flags.

Validation checks:

- Every report claim has at least one evidence ID.
- Every evidence ID exists in the registry.
- Every numeric input is traceable to a cited page and snippet.
- Arithmetic is internally consistent.
- Older evidence is not used when superseded by newer clear evidence.
- Newer documents without dividend information do not incorrectly invalidate older clear sources.
- Ambiguous source periods are flagged.
- Missing external data is flagged.
- LLM-generated unsupported facts are rejected.

### HTML Report Skill

Input:

- Validated report model.

Output:

- `dividend-report.html` in the analyzed company folder.

Sections:

1. Executive summary.
2. Scenario estimates.
3. Latest dividend source.
4. Evidence table.
5. Manual-review flags.
6. Reasoning tree appendix.
7. Superseded evidence appendix.
8. Unavailable or failed PDF parsing appendix.

The report should be readable as a standalone HTML file and should not require a running server.

## Report Behavior

The executive summary should show:

- Company folder analyzed.
- Latest clear dividend source.
- Estimated dividend per share or "cannot estimate."
- Scenario range when supported.
- Confidence.
- Manual-review status.

The scenario table should show:

- Scenario name.
- Estimate.
- Formula.
- Cited inputs.
- Missing inputs.
- Confidence.
- Review flags.

The latest dividend source section should explain recency decisions in plain language. Example:

```text
Q1 2026 contained no clear dividend statement. The FY2025 annual report is the latest clear dividend source and is used for the current estimate.
```

The superseded evidence appendix should preserve older evidence with an explanation such as:

```text
Q2 2025 dividend statement superseded by Q4 2025 statement for the same dividend period.
```

## Error Handling

- If one PDF cannot be parsed, continue with the remaining PDFs and list the failed PDF in the report.
- If all PDFs fail parsing, write an error report instead of an estimate report.
- If document date, reporting-period, or dividend-period inference conflicts, flag affected evidence for manual review.
- If a dividend phrase lacks a clear amount or formula, store it as qualitative evidence, not a numeric input.
- If validation rejects all numeric branches, produce a "cannot estimate" report with evidence and flags.
- If share price is missing from the PDFs, do not calculate dividend yield and add a missing external data flag.

## Testing Plan

Test cases should include:

- Q1 report has no dividend information, annual report has the latest clear dividend information.
- Q4 report supersedes an older Q2 dividend statement.
- Newer document contains no dividend statement and should not invalidate older clear evidence.
- Payout-ratio branch uses cited EPS and cited payout ratio.
- Partial-year earnings are treated as a floor unless full-year guidance is cited.
- Missing current share price prevents dividend-yield calculation.
- Document date ambiguity triggers manual review.
- LLM returns an uncited claim and validation rejects it.
- Different `LLMAdapter` implementations satisfy the same structured contracts.
- PDF parsing failure is surfaced without stopping analysis of other documents.

## Acceptance Criteria

- Running the CLI on one company folder creates `dividend-report.html` in that folder.
- The report contains only claims supported by citations from provided PDFs.
- The workflow identifies the latest clear dividend source even when newer PDFs have no dividend information.
- Older conflicting dividend evidence is marked superseded and excluded from the main estimate.
- Missing share price, forecasts, EPS, or payout information is flagged rather than guessed.
- The workflow can swap LLM providers or agent frameworks through adapters without changing skill contracts.
- Validation can reject unsupported LLM output before report generation.
