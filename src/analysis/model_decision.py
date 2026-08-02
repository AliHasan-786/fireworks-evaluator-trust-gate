from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any

from src.evaluators.deterministic import evaluate_prediction
from src.schemas import EvaluationCase, RunRecord


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentile
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def summarize_model(records: list[RunRecord], cases: dict[str, EvaluationCase]) -> dict[str, Any]:
    answerable: list[bool] = []
    ambiguous: list[bool] = []
    schema: list[bool] = []
    latencies: list[float] = []
    costs: list[float] = []
    errors = 0
    for record in records:
        case = cases[record.case_id]
        latencies.append(record.latency_ms)
        if record.estimated_cost_usd is not None:
            costs.append(record.estimated_cost_usd)
        if record.parsed_response is None:
            schema.append(False)
            errors += 1
            if case.needs_clarification:
                ambiguous.append(False)
            else:
                answerable.append(False)
            continue
        result = evaluate_prediction(case, record.parsed_response.model_dump())
        schema.append(result.schema_valid)
        if case.needs_clarification:
            ambiguous.append(result.clarification_correct)
        else:
            answerable.append(result.intent_correct is True)

    def ratio(values: list[bool]) -> float | None:
        return sum(values) / len(values) if values else None

    return {
        "n": len(records),
        "intent_accuracy": ratio(answerable),
        "ambiguity_detection": ratio(ambiguous),
        "json_reliability": ratio(schema),
        "api_or_parse_errors": errors,
        "p50_latency_ms": median(latencies) if latencies else None,
        "p95_latency_ms": _percentile(latencies, 0.95),
        "estimated_cost_per_1000_cases_usd": (sum(costs) / len(costs) * 1000)
        if costs and len(costs) == len(records)
        else None,
    }


def compare_models(records: list[RunRecord], cases: dict[str, EvaluationCase]) -> dict[str, Any]:
    grouped: dict[str, list[RunRecord]] = defaultdict(list)
    for record in records:
        grouped[record.model_id].append(record)
    summaries = {model: summarize_model(group, cases) for model, group in grouped.items()}
    complete = [model for model, summary in summaries.items() if summary["n"] == len(cases)]
    if len(complete) < 2:
        recommendation = "NO_DEPLOY: a complete fast/strong comparison is not available."
    else:
        eligible = [
            model
            for model in complete
            if summaries[model]["json_reliability"] >= 0.99
            and summaries[model]["ambiguity_detection"] is not None
            and summaries[model]["ambiguity_detection"] >= 0.90
        ]
        if not eligible:
            recommendation = "NO_DEPLOY: no model meets reliability and ambiguity guardrails."
        else:
            default = min(eligible, key=lambda model: summaries[model]["p50_latency_ms"])
            strongest = max(
                eligible,
                key=lambda model: (
                    summaries[model]["intent_accuracy"],
                    summaries[model]["ambiguity_detection"],
                ),
            )
            recommendation = (
                f"DEFAULT {default}; escalate low-confidence or clarification cases to {strongest}."
            )
    return {
        "models": summaries,
        "recommendation": recommendation,
        "decision_method": "Guardrails first, then latency for the default and quality for escalation; no weighted composite.",
    }
