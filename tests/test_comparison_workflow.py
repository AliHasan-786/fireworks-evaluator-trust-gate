import json
from datetime import UTC, datetime
from pathlib import Path

from src.cli import load_cases, select_smoke_cases
from src.inference.model_catalog import load_run_config
from src.reporting.comparison import generate_comparison_artifacts
from src.schemas import EvaluationCase, ModelPrediction, RunRecord, TokenUsage


def _case(case_id: str = "case-1") -> EvaluationCase:
    return EvaluationCase(
        case_id=case_id,
        user_message="Where is my card?",
        expected_intent="card_arrival",
        needs_clarification=False,
        source_type="banking77_standard",
        notes="test fixture",
    )


def _record(case_id: str, model_id: str, latency_ms: float) -> RunRecord:
    now = datetime.now(UTC)
    return RunRecord(
        case_id=case_id,
        model_id=model_id,
        started_at=now,
        completed_at=now,
        latency_ms=latency_ms,
        attempts=1,
        usage=TokenUsage(prompt_tokens=100, completion_tokens=20, total_tokens=120),
        estimated_cost_usd=0.0001,
        raw_response='{"predicted_intent":"card_arrival"}',
        parsed_response=ModelPrediction(
            predicted_intent="card_arrival",
            confidence=0.95,
            needs_clarification=False,
            rationale="The user is asking about delivery timing.",
        ),
    )


def test_checked_in_comparison_config_is_bounded_and_distinct():
    _raw, config = load_run_config(Path("config/run.v1.yaml"))
    ordered = config.ordered_models()
    assert config.hard_spend_cap_usd == 6
    assert [alias for alias, _spec in ordered] == ["fast", "strong"]
    assert len({spec.model_id for _alias, spec in ordered}) == 2


def test_smoke_slice_includes_standard_difficult_and_ambiguous_cases():
    cases = load_cases(Path("data/processed/v1.0.0/evaluation_set.jsonl"))
    smoke = select_smoke_cases(cases)
    assert len(smoke) == 5
    assert {case.source_type for case in smoke} == {
        "banking77_standard",
        "banking77_difficult",
        "authored_ambiguous",
    }


def test_comparison_artifacts_are_generated_only_from_saved_records(tmp_path):
    _raw, config = load_run_config(Path("config/run.v1.yaml"))
    cases = [_case()]
    model_files = {}
    for alias, spec in config.ordered_models():
        path = tmp_path / f"{alias}.jsonl"
        path.write_text(_record("case-1", spec.model_id, 10 if alias == "fast" else 20).model_dump_json() + "\n")
        model_files[alias] = path

    json_output = tmp_path / "output/comparison.json"
    memo_output = tmp_path / "reports/memo.md"
    site_output = tmp_path / "site/comparison.json"
    artifact = generate_comparison_artifacts(
        cases,
        model_files,
        config,
        dataset_sha256="abc123",
        json_output=json_output,
        memo_output=memo_output,
        site_output=site_output,
    )

    assert artifact["coverage"]["fast"]["canonical_cases"] == 1
    assert artifact["coverage"]["strong"]["canonical_cases"] == 1
    assert artifact["coverage"]["total_recorded_spend_usd"] == 0.0002
    assert artifact["comparison"]["recommendation"] == (
        "NO_DEPLOY: no model meets reliability and ambiguity guardrails."
    )
    site = json.loads(site_output.read_text())
    assert site["comparison"] == artifact["comparison"]
    assert site["examples"] == []
    assert "Human-evidence boundary" in memo_output.read_text()
