import csv
from datetime import UTC, datetime

import pytest
from conftest import load_dataset

from src.human_labeling.calibration import evaluate_completed_packet, packet_responses
from src.human_labeling.export import export_packet, select_blind_cases
from src.human_labeling.import_labels import import_labels
from src.schemas import ModelPrediction, RunRecord


def test_blind_packet_contains_no_scores_and_required_mix(tmp_path):
    output = tmp_path / "packet.csv"
    export_packet(load_dataset(), "blind-model-a", output)
    rows = list(csv.DictReader(output.open()))
    assert len(rows) == 30
    assert "predicted_intent" not in rows[0] and "judge_score" not in rows[0]
    assert sum(row["case_id"].startswith("amb-") for row in rows) == 20


def test_import_requires_failure_category(tmp_path):
    path = tmp_path / "labels.csv"
    path.write_text("model_id,case_id,human_outcome,failure_category,notes\nm,c,fail,,x\n")
    with pytest.raises(ValueError, match="failure_category"):
        import_labels(path)


def test_import_rejects_failure_category_on_pass(tmp_path):
    path = tmp_path / "labels.csv"
    path.write_text(
        "model_id,case_id,human_outcome,failure_category,notes\nm,c,pass,wrong_intent,x\n"
    )
    with pytest.raises(ValueError, match="passing cases cannot have failure_category"):
        import_labels(path)


def _completed_evidence(tmp_path):
    cases = load_dataset()
    selected = select_blind_cases(cases)
    model_id = "accounts/example/models/calibrated"
    failing_ids = {case.case_id for case in selected if not case.needs_clarification}
    failing_ids = set(sorted(failing_ids)[:5])
    responses = {}
    records = []
    now = datetime.now(UTC)
    for case in selected:
        if case.case_id in failing_ids:
            prediction = ModelPrediction(
                predicted_intent="wrong_intent",
                confidence=0.9,
                needs_clarification=False,
                rationale="incorrect route",
            )
        elif case.needs_clarification:
            prediction = ModelPrediction(
                predicted_intent=None,
                confidence=0.3,
                needs_clarification=True,
                rationale="key routing detail is missing",
            )
        else:
            prediction = ModelPrediction(
                predicted_intent=case.expected_intent,
                confidence=0.9,
                needs_clarification=False,
                rationale="specific route",
            )
        raw = prediction.model_dump_json()
        responses[case.case_id] = raw
        records.append(
            RunRecord(
                case_id=case.case_id,
                model_id=model_id,
                started_at=now,
                completed_at=now,
                latency_ms=1,
                attempts=1,
                raw_response=raw,
                parsed_response=prediction,
            )
        )
    run_path = tmp_path / "runs.jsonl"
    run_path.write_text("".join(record.model_dump_json() + "\n" for record in records))
    packet_path = tmp_path / "completed.csv"
    export_packet(cases, model_id, packet_path, responses)
    with packet_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if row["case_id"] in failing_ids:
            row["human_outcome"] = "fail"
            row["failure_category"] = "wrong_intent"
        else:
            row["human_outcome"] = "pass"
    with packet_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return cases, packet_path, run_path


def test_completed_packet_runs_end_to_end_gate(tmp_path):
    cases, packet_path, run_path = _completed_evidence(tmp_path)
    config = {
        "version": "test",
        "minimum_human_cases": 30,
        "minimum_human_failures": 5,
        "minimum_agreement": 0.85,
        "minimum_failure_recall": 0.9,
        "maximum_leniency_rate": 0.1,
        "bootstrap_iterations": 50,
        "bootstrap_seed": 7,
    }
    decision, analysis = evaluate_completed_packet(cases, packet_path, run_path, config)
    assert decision.decision == "PASS"
    assert analysis["overall"]["n"] == 30
    assert analysis["overall"]["human_failures"] == 5
    assert analysis["overall"]["failure_recall"] == 1


def test_completed_packet_rejects_tampered_evidence(tmp_path):
    cases, packet_path, run_path = _completed_evidence(tmp_path)
    text = packet_path.read_text()
    packet_path.write_text(text.replace("key routing detail is missing", "tampered", 1))
    with pytest.raises(ValueError, match="source evidence|evidence_sha256"):
        evaluate_completed_packet(
            cases,
            packet_path,
            run_path,
            {
                "version": "test",
                "minimum_human_cases": 30,
                "minimum_human_failures": 5,
                "minimum_agreement": 0.85,
                "minimum_failure_recall": 0.9,
                "maximum_leniency_rate": 0.1,
                "bootstrap_iterations": 10,
            },
        )


def test_packet_responses_requires_all_30_successes(tmp_path):
    cases, _packet_path, run_path = _completed_evidence(tmp_path)
    lines = run_path.read_text().splitlines()
    run_path.write_text("\n".join(lines[:-1]) + "\n")
    with pytest.raises(ValueError, match="missing 1 cases"):
        packet_responses(cases, "accounts/example/models/calibrated", run_path)
