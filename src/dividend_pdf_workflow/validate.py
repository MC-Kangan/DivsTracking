from __future__ import annotations

from .models import ReportModel


def validate_report_model(report: ReportModel) -> ReportModel:
    known_ids = {item.id for item in report.evidence}
    rejected = list(report.rejected_claims)
    flags = list(report.manual_review_flags)

    for scenario in report.scenarios:
        for evidence_id in scenario.evidence_ids:
            if evidence_id not in known_ids:
                rejected.append(f"missing evidence id: {evidence_id}")

    if not any(item.kind == "share_price" for item in report.evidence):
        flag = "Missing external data: share price not found in provided PDFs; dividend yield not calculated."
        if flag not in flags:
            flags.append(flag)

    for item in report.ranking.manual_review:
        if item not in flags:
            flags.append(item)

    report.rejected_claims = rejected
    report.manual_review_flags = flags
    return report
