from __future__ import annotations

from html import escape

from .models import EvidenceItem, ReportModel, Scenario


def render_html_report(report: ReportModel) -> str:
    selected = report.ranking.selected_source
    selected_text = (
        f"{escape(selected.document)} page {selected.page}: {escape(selected.snippet)}"
        if selected
        else "No latest clear dividend source found."
    )
    summary_estimate = report.scenarios[0].estimate if report.scenarios else "cannot estimate"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(report.company)} Dividend Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #1f2933; line-height: 1.5; }}
    h1, h2 {{ color: #102a43; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 28px; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f0f4f8; }}
    .flag {{ background: #fff7ed; border-left: 4px solid #f97316; padding: 8px 12px; margin: 8px 0; }}
    .ok {{ background: #ecfdf5; border-left: 4px solid #10b981; padding: 8px 12px; margin: 8px 0; }}
    code {{ background: #f0f4f8; padding: 1px 4px; }}
  </style>
</head>
<body>
  <h1>{escape(report.company)} Dividend Report</h1>
  <h2>Executive Summary</h2>
  <p><strong>Estimated dividend:</strong> {escape(summary_estimate)}</p>
  <p><strong>Latest clear source:</strong> {selected_text}</p>
  <p><strong>Confidence:</strong> {escape(report.scenarios[0].confidence if report.scenarios else "low")}</p>

  <h2>Scenario Estimates</h2>
  {_render_scenarios(report.scenarios)}

  <h2>Latest Dividend Source</h2>
  <p>{escape(report.ranking.explanation)}</p>

  <h2>Evidence Table</h2>
  {_render_evidence(report.evidence)}

  <h2>Manual Review</h2>
  {_render_flags(report.manual_review_flags)}

  <h2>Reasoning Tree</h2>
  {_render_reasoning(report.scenarios)}

  <h2>Superseded Evidence</h2>
  {_render_superseded(report.ranking.superseded)}

  <h2>Unavailable Or Failed PDF Parsing</h2>
  {_render_failed_documents(report)}
</body>
</html>
"""


def _render_scenarios(scenarios: list[Scenario]) -> str:
    rows = []
    for scenario in scenarios:
        rows.append(
            "<tr>"
            f"<td>{escape(scenario.name)}</td>"
            f"<td>{escape(scenario.estimate)}</td>"
            f"<td>{escape(scenario.formula)}</td>"
            f"<td>{escape(', '.join(scenario.evidence_ids))}</td>"
            f"<td>{escape(', '.join(scenario.missing_inputs) or 'none')}</td>"
            f"<td>{escape(scenario.confidence)}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>Scenario</th><th>Estimate</th><th>Formula</th><th>Citations</th><th>Missing Inputs</th><th>Confidence</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def _render_evidence(evidence: list[EvidenceItem]) -> str:
    rows = []
    for item in evidence:
        rows.append(
            "<tr>"
            f"<td><code>{escape(item.id)}</code></td>"
            f"<td>{escape(item.kind)}</td>"
            f"<td>{escape(str(item.value) if item.value is not None else '')} {escape(item.unit or '')}</td>"
            f"<td>{escape(item.document)} p.{item.page}</td>"
            f"<td>{escape(item.dividend_period or '')}</td>"
            f"<td>{escape(item.snippet)}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>ID</th><th>Kind</th><th>Value</th><th>Source</th><th>Dividend Period</th><th>Snippet</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"


def _render_flags(flags: list[str]) -> str:
    if not flags:
        return '<div class="ok">No manual review flags.</div>'
    return "".join(f'<div class="flag">{escape(flag)}</div>' for flag in flags)


def _render_reasoning(scenarios: list[Scenario]) -> str:
    if not scenarios:
        return "<p>No reasoning branches generated.</p>"
    items = []
    for scenario in scenarios:
        items.append(
            f"<li><strong>{escape(scenario.name)}</strong>: {escape(scenario.formula)} "
            f"using {escape(', '.join(scenario.evidence_ids) or 'no evidence')}.</li>"
        )
    return "<ul>" + "".join(items) + "</ul>"


def _render_superseded(evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return "<p>No superseded evidence identified.</p>"
    return "<ul>" + "".join(
        f"<li><code>{escape(item.id)}</code> superseded by <code>{escape(item.superseded_by or '')}</code>.</li>"
        for item in evidence
    ) + "</ul>"


def _render_failed_documents(report: ReportModel) -> str:
    failed = [doc for doc in report.documents if doc.parse_error]
    if not failed:
        return "<p>No PDF parsing failures.</p>"
    return "<ul>" + "".join(f"<li>{escape(doc.filename)}: {escape(doc.parse_error or '')}</li>" for doc in failed) + "</ul>"
