from __future__ import annotations

from .models import EvidenceItem, RankingResult, Scenario


def build_scenarios(evidence: list[EvidenceItem], ranking: RankingResult) -> list[Scenario]:
    if not ranking.selected_source:
        return [
            Scenario(
                name="cannot estimate",
                estimate="cannot estimate from provided documents",
                formula="No latest clear dividend source was found.",
                evidence_ids=[],
                missing_inputs=["latest clear dividend source"],
                confidence="low",
                flags=["Manual review required."],
            )
        ]

    selected = ranking.selected_source
    unit = selected.unit or "per share"
    estimate = _format_estimate(selected.value, unit)
    missing_inputs = []
    if not any(item.kind == "share_price" for item in evidence):
        missing_inputs.append("share price")

    scenarios = [
        Scenario(
            name="confirmed/minimum",
            estimate=estimate,
            formula="latest clear dividend per share",
            evidence_ids=[selected.id],
            missing_inputs=missing_inputs,
            confidence=selected.confidence,
            arithmetic=f"{selected.value:g} {unit}" if selected.value is not None else None,
        )
    ]

    payout = _first(evidence, "dividend_payout_ratio")
    eps = _first(evidence, "earnings_per_share")
    if payout and eps and payout.value is not None and eps.value is not None:
        calculated = eps.value * payout.value / 100.0
        scenarios.append(
            Scenario(
                name="base case",
                estimate=f"EUR {calculated:.2f}/share",
                formula="earnings per share * payout ratio",
                evidence_ids=[eps.id, payout.id],
                missing_inputs=missing_inputs,
                confidence="medium",
                arithmetic=f"{eps.value:g} * {payout.value:g}% = {calculated:.2f}",
            )
        )

    scenarios.append(
        Scenario(
            name="optimistic",
            estimate=estimate,
            formula="No cited upside driver found; reuse latest clear dividend source.",
            evidence_ids=[selected.id],
            missing_inputs=missing_inputs + ["cited full-year upside guidance"],
            confidence="low",
            flags=["Optimistic case is capped by missing cited forecast inputs."],
            arithmetic=f"{selected.value:g} {unit}" if selected.value is not None else None,
        )
    )
    return scenarios


def _first(evidence: list[EvidenceItem], kind: str) -> EvidenceItem | None:
    for item in evidence:
        if item.kind == kind:
            return item
    return None


def _format_estimate(value: float | None, unit: str) -> str:
    if value is None:
        return "cannot estimate"
    if unit == "EUR/share":
        return f"EUR {value:.2f}/share"
    return f"{value:g} {unit}"
