# Dividend PDF Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python command-line workflow that analyzes one company folder of PDFs and writes a cited `dividend-report.html`.

**Architecture:** The implementation uses deterministic Python modules for ingestion, evidence extraction, ranking, scenario construction, validation, and HTML rendering. LLM and agent portability is represented by a stable adapter protocol; the first version runs without a live LLM by using deterministic heuristics and validating every claim.

**Tech Stack:** Python 3, `pdfplumber` for PDF text/table extraction, standard-library `dataclasses`, `argparse`, `html`, `json`, `re`, and `unittest`.

---

## File Structure

- Create `src/dividend_pdf_workflow/models.py`: shared dataclasses and serialization helpers.
- Create `src/dividend_pdf_workflow/llm.py`: portable `LLMAdapter` protocol and no-op deterministic adapter.
- Create `src/dividend_pdf_workflow/ingest.py`: PDF ingestion and metadata inference.
- Create `src/dividend_pdf_workflow/extract.py`: dividend evidence extraction from parsed pages.
- Create `src/dividend_pdf_workflow/rank.py`: latest clear source and supersession ranking.
- Create `src/dividend_pdf_workflow/reason.py`: scenario construction from cited evidence only.
- Create `src/dividend_pdf_workflow/validate.py`: deterministic validation of citations, supersession, and arithmetic inputs.
- Create `src/dividend_pdf_workflow/report.py`: standalone HTML report renderer.
- Create `src/dividend_pdf_workflow/cli.py`: command-line entry point.
- Create `src/dividend_pdf_workflow/__init__.py`: package marker and version.
- Create `scripts/analyze_dividends.py`: executable wrapper.
- Create `tests/test_workflow.py`: unit tests covering recency, supersession, missing external data, validation, and HTML output.

## Tasks

### Task 1: Models And Adapter Contracts

**Files:**
- Create: `src/dividend_pdf_workflow/models.py`
- Create: `src/dividend_pdf_workflow/llm.py`
- Create: `src/dividend_pdf_workflow/__init__.py`
- Test: `tests/test_workflow.py`

- [ ] **Step 1: Write failing tests for model serialization and adapter protocol**

```python
from dividend_pdf_workflow.models import EvidenceItem
from dividend_pdf_workflow.llm import DeterministicLLMAdapter

def test_evidence_item_serializes_with_dividend_period(self):
    item = EvidenceItem(
        id="BMW-annual-2025-p10-dividend",
        company="BMW",
        document="annual.pdf",
        document_type="annual_report",
        reporting_period="FY2025",
        dividend_period="FY2025",
        publication_date="2026-03",
        page=10,
        kind="declared_dividend_per_share",
        value=4.30,
        unit="EUR/share",
        snippet="Dividend proposed: EUR 4.30 per share.",
        confidence="high",
    )
    self.assertEqual(item.to_dict()["dividend_period"], "FY2025")

def test_deterministic_adapter_returns_schema_safe_empty_result(self):
    adapter = DeterministicLLMAdapter()
    self.assertEqual(adapter.generate_structured("prompt", {"type": "object"}, {}), {})
```

- [ ] **Step 2: Run test and verify failure**

Run: `PYTHONPATH=src python3 -m unittest tests.test_workflow -v`
Expected: import failure because package files do not exist.

- [ ] **Step 3: Implement dataclasses and adapter**

Create immutable-enough dataclasses for documents, pages, evidence, ranking, scenarios, validation results, and report model. Implement `to_dict()` helpers using `dataclasses.asdict()`.

- [ ] **Step 4: Run test and verify pass**

Run: `PYTHONPATH=src python3 -m unittest tests.test_workflow -v`
Expected: tests pass.

### Task 2: Ranking And Validation

**Files:**
- Create: `src/dividend_pdf_workflow/rank.py`
- Create: `src/dividend_pdf_workflow/validate.py`
- Modify: `tests/test_workflow.py`

- [ ] **Step 1: Write failing tests for latest clear source, supersession, and uncited rejection**

Test cases:

- Q1 2026 has no dividend evidence and FY2025 annual report has a dividend; FY2025 is selected.
- Q4 2025 supersedes Q2 2025 for the same dividend period.
- A scenario branch referencing a missing evidence ID is rejected.

- [ ] **Step 2: Run test and verify failure**

Run: `PYTHONPATH=src python3 -m unittest tests.test_workflow -v`
Expected: missing ranking and validation functions.

- [ ] **Step 3: Implement ranking and validation**

Implement `rank_dividend_sources(evidence, documents)` and `validate_report_model(report_model)`. Ranking should sort by dividend period, publication date, and document type priority. Validation should reject branches with missing evidence IDs and add missing external data flags when dividend yield cannot be calculated.

- [ ] **Step 4: Run test and verify pass**

Run: `PYTHONPATH=src python3 -m unittest tests.test_workflow -v`
Expected: tests pass.

### Task 3: Extraction And Reasoning

**Files:**
- Create: `src/dividend_pdf_workflow/extract.py`
- Create: `src/dividend_pdf_workflow/reason.py`
- Modify: `tests/test_workflow.py`

- [ ] **Step 1: Write failing tests for dividend extraction and scenario creation**

Test cases:

- Extract `EUR 4.30 per share` from dividend wording with page citation.
- Extract payout ratio and EPS evidence.
- Scenario builder creates confirmed/minimum scenario from declared dividend.
- Scenario builder does not calculate yield without share price evidence.

- [ ] **Step 2: Run test and verify failure**

Run: `PYTHONPATH=src python3 -m unittest tests.test_workflow -v`
Expected: missing extraction and reasoning functions.

- [ ] **Step 3: Implement extraction and reasoning**

Use conservative regex patterns for dividend-per-share, payout ratio, EPS, and share price only when dividend-related terms or financial metric terms appear nearby. Reasoning must use selected ranking output and evidence IDs only.

- [ ] **Step 4: Run test and verify pass**

Run: `PYTHONPATH=src python3 -m unittest tests.test_workflow -v`
Expected: tests pass.

### Task 4: PDF Ingestion, CLI, And HTML Report

**Files:**
- Create: `src/dividend_pdf_workflow/ingest.py`
- Create: `src/dividend_pdf_workflow/report.py`
- Create: `src/dividend_pdf_workflow/cli.py`
- Create: `scripts/analyze_dividends.py`
- Modify: `tests/test_workflow.py`

- [ ] **Step 1: Write failing tests for report rendering and CLI orchestration**

Test cases:

- HTML renderer includes executive summary, latest source explanation, evidence table, manual flags, reasoning tree, and superseded evidence.
- CLI orchestration writes `dividend-report.html` for a folder when supplied parsed documents through the workflow functions.

- [ ] **Step 2: Run test and verify failure**

Run: `PYTHONPATH=src python3 -m unittest tests.test_workflow -v`
Expected: missing ingestion, renderer, and CLI functions.

- [ ] **Step 3: Implement ingestion, rendering, and CLI**

Use `pdfplumber` to parse pages and tables. Inference should identify document type, reporting period, and publication date from filenames and text hints. The report must be a standalone HTML file with escaped snippets and clear manual-review flags.

- [ ] **Step 4: Run test and verify pass**

Run: `PYTHONPATH=src python3 -m unittest tests.test_workflow -v`
Expected: tests pass.

### Task 5: End-To-End Verification On Provided PDFs

**Files:**
- Generated: `BMW/dividend-report.html`
- Generated: `MBG/dividend-report.html`
- Modify only if needed: implementation files above.

- [ ] **Step 1: Run all tests**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: all tests pass.

- [ ] **Step 2: Run CLI for BMW**

Run: `PYTHONPATH=src python3 scripts/analyze_dividends.py BMW`
Expected: `BMW/dividend-report.html` is written.

- [ ] **Step 3: Run CLI for MBG**

Run: `PYTHONPATH=src python3 scripts/analyze_dividends.py MBG`
Expected: `MBG/dividend-report.html` is written.

- [ ] **Step 4: Inspect generated report text**

Run: `rg -n "Executive Summary|Latest Dividend Source|Manual Review|Superseded Evidence|Missing external data" BMW/dividend-report.html MBG/dividend-report.html`
Expected: both reports contain the core sections and missing external data flags when share price is absent.

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add docs/superpowers/plans/2026-06-29-dividend-pdf-workflow.md src scripts tests BMW/dividend-report.html MBG/dividend-report.html
git commit -m "Implement dividend PDF workflow"
```

Expected: implementation commit is created.

