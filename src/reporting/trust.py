from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.evaluators.deterministic import evaluate_prediction
from src.human_labeling.calibration import evaluate_completed_packet, load_successful_records
from src.human_labeling.export import select_blind_cases
from src.human_labeling.import_labels import import_labels
from src.schemas import EvaluationCase


def _percent(value: float | None) -> str:
    return "Undefined" if value is None else f"{value:.1%}"


def _interval(value: list[float] | tuple[float, float] | None) -> str:
    if value is None:
        return "Undefined"
    return f"{value[0]:.1%} to {value[1]:.1%}"


def _source_label(value: str) -> str:
    return {
        "authored_ambiguous": "Authored ambiguous",
        "banking77_difficult": "Banking77 difficult",
        "banking77_standard": "Banking77 standard",
    }.get(value, value)


def _trust_report(artifact: dict[str, Any]) -> str:
    gate = artifact["gate"]
    overall = artifact["analysis"]["overall"]
    thresholds = artifact["thresholds"]
    matrix = overall["confusion_matrix"]
    lines = [
        "# Evaluator trust report",
        "",
        f"**Decision: {gate['decision']}**",
        "",
        "The evidence is sufficient to make a gate decision, but the evaluator does not pass. "
        "It caught every human-identified failure in this pilot and never passed a response the reviewer failed; "
        "however, it rejected seven responses the reviewer accepted, reducing agreement below the versioned threshold.",
        "",
        "## Gate result",
        "",
        "| Criterion | Observed | Required | Result |",
        "|---|---:|---:|---|",
        f"| Validated human labels | {overall['n']} | >= {thresholds['minimum_human_cases']} | PASS |",
        f"| Human-identified failures | {overall['human_failures']} | >= {thresholds['minimum_human_failures']} | PASS |",
        f"| Agreement | {_percent(overall['agreement'])} | >= {_percent(thresholds['minimum_agreement'])} | FAIL |",
        f"| Failure recall | {_percent(overall['failure_recall'])} | >= {_percent(thresholds['minimum_failure_recall'])} | PASS |",
        f"| Leniency rate | {_percent(overall['leniency_rate'])} | <= {_percent(thresholds['maximum_leniency_rate'])} | PASS |",
        "",
        "Gate reason: " + "; ".join(gate["reasons"]),
        "",
        "## Confusion matrix",
        "",
        "| Human / automated | Automated pass | Automated fail |",
        "|---|---:|---:|",
        f"| Human pass | {matrix['human_pass_auto_pass']} | {matrix['human_pass_auto_fail']} |",
        f"| Human fail | {matrix['human_fail_auto_pass']} | {matrix['human_fail_auto_fail']} |",
        "",
        f"Agreement bootstrap interval: {_interval(overall['agreement_ci'])}. "
        f"Failure-recall interval: {_interval(overall['failure_recall_ci'])}.",
        "",
        "## Traceable disagreements",
        "",
        "All observed disagreements point in the same direction: the automated evaluator was stricter than the reviewer.",
        "",
    ]
    for item in artifact["disagreements"]:
        reasons = "; ".join(item["automated_failure_reasons"])
        lines.extend(
            [
                f"### `{item['case_id']}` — {_source_label(item['source_type'])}",
                "",
                f"> {item['user_message']}",
                "",
                f"- Human outcome: **{item['human_outcome'].upper()}**",
                f"- Automated outcome: **{'PASS' if item['automated_pass'] else 'FAIL'}**",
                f"- Direction: `{item['direction']}`",
                f"- Automated reason: {reasons}",
                "",
            ]
        )
    lines.extend(
        [
            "## Subgroups",
            "",
            "| Source | n | Human failures | Agreement | Failure recall | Leniency | Strictness |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for source, metrics in artifact["analysis"]["by_source_type"].items():
        lines.append(
            f"| {_source_label(source)} | {metrics['n']} | {metrics['human_failures']} | "
            f"{_percent(metrics['agreement'])} | {_percent(metrics['failure_recall'])} | "
            f"{_percent(metrics['leniency_rate'])} | {_percent(metrics['strictness_rate'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation and next action",
            "",
            "The failure mode is over-rejection, not missed reviewer failures. Before automation, revise the deterministic "
            "rubric so plausible intent choices on under-specified messages are not automatically treated as failures, "
            "then run a new blinded packet. Preserve the current thresholds; changing them after seeing the result would "
            "invalidate the gate.",
            "",
            "## Limitations",
            "",
            "- This is one non-expert family reviewer who completed a quick informal blind pass; it is not a domain-expert study and does not measure inter-rater reliability.",
            "- Failure recall is based on five human failures, the minimum allowed denominator. The apparent 100% recall is encouraging but imprecise.",
            "- Banking77 and authored ambiguity cases are proxies, not Fireworks customer production traffic.",
            "- The result validates this evaluator/model/dataset snapshot only; it is not general certification.",
            f"- Label evidence SHA-256: `{artifact['evidence']['human_labels_sha256']}`.",
            f"- Generated at `{artifact['generated_at']}` from saved run records; no live call is needed to reproduce it.",
            "",
        ]
    )
    return "\n".join(lines)


def _design_partner_readout(artifact: dict[str, Any]) -> str:
    overall = artifact["analysis"]["overall"]
    return "\n".join(
        [
            "# Design-partner readout",
            "",
            "## Executive decision",
            "",
            f"The v1 evaluator trust gate is **{artifact['gate']['decision']}**. One non-expert family reviewer completed a quick informal 30-case blind pass that produced "
            f"{_percent(overall['agreement'])} agreement against an {_percent(artifact['thresholds']['minimum_agreement'])} requirement. "
            f"It recalled {overall['human_failures']} of {overall['human_failures']} human failures and produced zero false passes, "
            "but it false-failed seven reviewer-accepted responses.",
            "",
            "## What we learned",
            "",
            "The evaluator's dominant risk is strictness. For an automated training loop this is safer than leniency, "
            "but it is still not trustworthy: rejecting reasonable outputs can teach a model to over-clarify and can distort product metrics.",
            "",
            "## Product recommendation",
            "",
            "Expose calibration as a first-class setup state with a confusion matrix and disagreement direction. "
            "The UI should distinguish `evaluator_too_strict` from `evaluator_too_lenient`, show the versioned threshold, "
            "and block automation on either insufficient evidence or a failed gate.",
            "",
            "## Proposed next design-partner cycle",
            "",
            "1. Adjudicate the seven strictness disagreements with a domain owner and revise the pass rubric without changing thresholds.",
            "2. Add customer-specific failure examples and loss weights.",
            "3. Run at least two independent reviewers, measure inter-rater agreement, and adjudicate conflicts blind to evaluator output.",
            "4. Repeat on a held-out packet before enabling retraining or deployment actions.",
            "",
            "## Boundary",
            "",
            "This is a public-data candidate proposal, not a claim about Fireworks' internal product roadmap or customer results.",
            "",
        ]
    )


def generate_trust_artifacts(
    cases: list[EvaluationCase],
    human_label_file: Path,
    run_record_file: Path,
    config: dict[str, Any],
    *,
    json_output: Path,
    report_output: Path,
    site_output: Path,
    readout_output: Path,
) -> dict[str, Any]:
    decision, analysis = evaluate_completed_packet(
        cases, human_label_file, run_record_file, config
    )
    labels = import_labels(human_label_file)
    model_id = labels[0].model_id
    records = load_successful_records(run_record_file, model_id)
    selected = {case.case_id: case for case in select_blind_cases(cases)}
    label_by_case = {label.case_id: label for label in labels}
    disagreements: list[dict[str, Any]] = []
    for case_id, case in selected.items():
        label = label_by_case[case_id]
        record = records[case_id]
        automated = evaluate_prediction(case, record.raw_response or "")
        human_pass = label.human_outcome == "pass"
        if human_pass == automated.passed:
            continue
        disagreements.append(
            {
                "case_id": case_id,
                "source_type": case.source_type,
                "user_message": case.user_message,
                "model_id": model_id,
                "model_response": record.raw_response,
                "human_outcome": label.human_outcome,
                "human_failure_category": label.failure_category,
                "automated_pass": automated.passed,
                "automated_failure_reasons": automated.failure_reasons,
                "direction": "evaluator_too_strict" if human_pass else "evaluator_too_lenient",
            }
        )
    thresholds = {
        key: config[key]
        for key in (
            "minimum_human_cases",
            "minimum_human_failures",
            "minimum_agreement",
            "minimum_failure_recall",
            "maximum_leniency_rate",
        )
    }
    artifact = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "gate": decision.model_dump(),
        "thresholds": thresholds,
        "evidence": {
            "reviewer_profile": "one non-expert family reviewer; quick informal blind pass",
            "human_labels_file": f"artifacts/human_labeling/{human_label_file.name}",
            "human_labels_sha256": hashlib.sha256(human_label_file.read_bytes()).hexdigest(),
            "run_records_file": f"artifacts/live/{run_record_file.name}",
            "model_id": model_id,
        },
        "analysis": analysis,
        "disagreements": disagreements,
        "limitations": [
            "one non-expert family reviewer; quick informal pass; no inter-rater reliability",
            "30-case pilot sample",
            "failure recall has a denominator of five",
            "public proxy distribution, not production traffic",
        ],
    }
    for output in (json_output, report_output, site_output, readout_output):
        output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    report_output.write_text(_trust_report(artifact), encoding="utf-8")
    site_output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    readout_output.write_text(_design_partner_readout(artifact), encoding="utf-8")
    return artifact
