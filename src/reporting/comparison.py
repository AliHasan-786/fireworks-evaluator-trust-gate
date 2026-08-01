from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.analysis.model_decision import compare_models
from src.evaluators.deterministic import evaluate_prediction
from src.inference.model_catalog import ComparisonRunConfig
from src.schemas import EvaluationCase, RunRecord


def _read_records(path: Path, expected_model_id: str) -> tuple[list[RunRecord], list[RunRecord]]:
    events: list[RunRecord] = []
    latest: dict[str, RunRecord] = {}
    if not path.exists():
        return events, []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = RunRecord.model_validate_json(line)
        if record.model_id != expected_model_id:
            raise ValueError(
                f"{path}: line {line_number} has model {record.model_id}, expected {expected_model_id}"
            )
        events.append(record)
        latest[record.case_id] = record
    return events, list(latest.values())


def _percent(value: float | None) -> str:
    return "Undefined" if value is None else f"{value:.1%}"


def _number(value: float | None, decimals: int = 1) -> str:
    return "Undefined" if value is None else f"{value:.{decimals}f}"


def _memo(artifact: dict[str, Any], aliases: dict[str, str]) -> str:
    comparison = artifact["comparison"]
    rows = []
    for metric, label, formatter in (
        ("intent_accuracy", "Intent accuracy", _percent),
        ("ambiguity_detection", "Ambiguity detection", _percent),
        ("json_reliability", "JSON reliability", _percent),
        ("api_or_parse_errors", "API / parse errors", lambda value: str(value)),
        ("p50_latency_ms", "p50 latency (ms)", _number),
        ("p95_latency_ms", "p95 latency (ms)", _number),
        (
            "estimated_cost_per_1000_cases_usd",
            "Estimated cost / 1,000 cases (USD)",
            lambda value: _number(value, 4),
        ),
    ):
        values = [formatter(comparison["models"].get(aliases[alias], {}).get(metric)) for alias in ("fast", "strong")]
        rows.append(f"| {label} | {values[0]} | {values[1]} |")
    coverage = artifact["coverage"]
    return "\n".join(
        [
            "# Model decision memo",
            "",
            f"Generated from saved run records at `{artifact['generated_at']}`.",
            "",
            "## Evidence",
            "",
            f"| Dimension | Fast: `{aliases['fast']}` | Strong: `{aliases['strong']}` |",
            "|---|---:|---:|",
            *rows,
            "",
            "## Coverage and spend",
            "",
            f"- Fast canonical cases: {coverage['fast']['canonical_cases']} / {coverage['expected_cases']}",
            f"- Strong canonical cases: {coverage['strong']['canonical_cases']} / {coverage['expected_cases']}",
            f"- Total recorded estimated spend: ${coverage['total_recorded_spend_usd']:.6f}",
            f"- Dataset SHA-256: `{artifact['dataset_sha256']}`",
            "",
            "## Recommendation",
            "",
            f"**{comparison['recommendation']}**",
            "",
            comparison["decision_method"],
            "",
            "## Human-evidence boundary",
            "",
            "This comparison measures model behavior against versioned ground truth. It does not establish evaluator-human alignment. The trust gate remains `INSUFFICIENT_EVIDENCE` until a completed, fingerprint-validated blind packet is returned by an independent reviewer.",
            "",
        ]
    )


def generate_comparison_artifacts(
    cases: list[EvaluationCase],
    model_files: dict[str, Path],
    config: ComparisonRunConfig,
    *,
    dataset_sha256: str,
    json_output: Path,
    memo_output: Path,
    site_output: Path,
) -> dict[str, Any]:
    case_ids = {case.case_id for case in cases}
    canonical: list[RunRecord] = []
    coverage: dict[str, Any] = {"expected_cases": len(cases)}
    aliases: dict[str, str] = {}
    latest_by_alias: dict[str, dict[str, RunRecord]] = {}
    total_spend = 0.0
    for alias, spec in config.ordered_models():
        aliases[alias] = spec.model_id
        events, latest = _read_records(model_files[alias], spec.model_id)
        latest_by_alias[alias] = {record.case_id: record for record in latest}
        unknown = sorted(record.case_id for record in latest if record.case_id not in case_ids)
        if unknown:
            raise ValueError(f"{alias} records contain unknown case IDs: {unknown}")
        canonical.extend(latest)
        spend = sum(record.estimated_cost_usd or 0.0 for record in events)
        total_spend += spend
        coverage[alias] = {
            "events": len(events),
            "canonical_cases": len(latest),
            "successful_cases": sum(record.parsed_response is not None for record in latest),
            "recorded_spend_usd": spend,
            "record_file": str(model_files[alias]),
        }
    coverage["total_recorded_spend_usd"] = total_spend
    artifact = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_sha256": dataset_sha256,
        "config_version": config.version,
        "pricing": {
            "verified_at": config.verified_at,
            "source": str(config.pricing_source),
            "models": {
                alias: spec.pricing_per_million_tokens.model_dump()
                for alias, spec in config.ordered_models()
            },
        },
        "coverage": coverage,
        "comparison": compare_models(canonical, {case.case_id: case for case in cases}),
    }
    rendered = json.dumps(artifact, indent=2) + "\n"
    strong_records = latest_by_alias["strong"]
    example_ids = ("amb-001", "amb-014", "dif-003")
    examples = []
    for case_id in example_ids:
        case = next((candidate for candidate in cases if candidate.case_id == case_id), None)
        record = strong_records.get(case_id)
        if case is None or record is None:
            continue
        automated = (
            evaluate_prediction(case, record.parsed_response.model_dump()).model_dump()
            if record.parsed_response is not None
            else None
        )
        examples.append(
            {
                "case_id": case.case_id,
                "source_type": case.source_type,
                "user_message": case.user_message,
                "model_id": record.model_id,
                "model_response": record.raw_response,
                "automated_evaluation": automated,
                "human_outcome": None,
            }
        )
    site_artifact = artifact | {"examples": examples}
    json_output.parent.mkdir(parents=True, exist_ok=True)
    memo_output.parent.mkdir(parents=True, exist_ok=True)
    site_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(rendered, encoding="utf-8")
    memo_output.write_text(_memo(artifact, aliases), encoding="utf-8")
    site_output.write_text(json.dumps(site_artifact, indent=2) + "\n", encoding="utf-8")
    return artifact
