from __future__ import annotations

from pathlib import Path
from typing import Any

from src.analysis.evaluator_trust import analyze_evaluator_trust
from src.evaluators.deterministic import evaluate_prediction
from src.gates.trust_gate import GateDecision, evaluate_gate
from src.human_labeling.export import select_blind_cases
from src.human_labeling.import_labels import import_labels
from src.schemas import EvaluationCase, RunRecord


def load_successful_records(path: Path, model_id: str) -> dict[str, RunRecord]:
    """Load one auditable successful response per case for a model."""
    if not path.exists():
        raise ValueError(f"run-record file does not exist: {path}")
    successful: dict[str, RunRecord] = {}
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = RunRecord.model_validate_json(line)
        except ValueError as exc:
            errors.append(f"line {line_number}: invalid run record: {exc}")
            continue
        if record.model_id != model_id or record.parsed_response is None:
            continue
        if record.case_id in successful:
            errors.append(
                f"line {line_number}: multiple successful records for {(model_id, record.case_id)}"
            )
            continue
        if record.raw_response is None:
            errors.append(f"line {line_number}: successful record has no raw_response")
            continue
        successful[record.case_id] = record
    if errors:
        raise ValueError("invalid run-record evidence:\n" + "\n".join(errors))
    return successful


def packet_responses(
    cases: list[EvaluationCase], model_id: str, run_record_file: Path
) -> dict[str, str]:
    records = load_successful_records(run_record_file, model_id)
    expected_ids = {case.case_id for case in select_blind_cases(cases)}
    missing = sorted(expected_ids - records.keys())
    if missing:
        raise ValueError(
            f"run records are incomplete for the blind packet: missing {len(missing)} cases: {missing}"
        )
    return {case_id: records[case_id].raw_response or "" for case_id in expected_ids}


def evaluate_completed_packet(
    cases: list[EvaluationCase],
    human_label_file: Path,
    run_record_file: Path,
    config: dict[str, Any],
) -> tuple[GateDecision, dict[str, Any]]:
    """Validate provenance, join evidence, compute trust metrics, and evaluate the gate."""
    preliminary = import_labels(human_label_file)
    model_ids = {label.model_id for label in preliminary}
    if len(model_ids) != 1:
        raise ValueError(f"a calibration packet must contain exactly one model_id; got {model_ids}")
    model_id = next(iter(model_ids))
    case_by_id = {case.case_id: case for case in cases}
    selected = select_blind_cases(cases)
    records = load_successful_records(run_record_file, model_id)
    expected_pairs = {(model_id, case.case_id) for case in selected}
    missing_records = sorted(case.case_id for case in selected if case.case_id not in records)
    if missing_records:
        raise ValueError(f"run records are incomplete for labeled cases: {missing_records}")

    expected_evidence = {
        (model_id, case.case_id): {
            "packet_order": index,
            "user_message": case.user_message,
            "model_response": records[case.case_id].raw_response,
        }
        for index, case in enumerate(selected, 1)
    }
    labels = import_labels(
        human_label_file,
        expected_pairs=expected_pairs,
        expected_evidence=expected_evidence,
    )
    automated_pass = {
        (model_id, case.case_id): evaluate_prediction(
            case, records[case.case_id].raw_response
        ).passed
        for case in selected
    }
    analysis = analyze_evaluator_trust(
        labels,
        automated_pass,
        case_by_id,
        iterations=int(config.get("bootstrap_iterations", 2000)),
        seed=int(config.get("bootstrap_seed", 20260731)),
    )
    decision = evaluate_gate(
        analysis["overall"], config, human_label_file=human_label_file
    )
    return decision, analysis
