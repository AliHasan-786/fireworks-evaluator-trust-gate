from src.analysis.evaluator_trust import analyze_evaluator_trust, bootstrap_interval, metric_bundle
from src.gates.trust_gate import evaluate_gate
from src.schemas import EvaluationCase, HumanLabel


def test_hand_checked_agreement_and_failure_recall():
    metrics = metric_bundle([True, True, False, False], [True, False, True, False])
    assert metrics["agreement"] == 0.5
    assert metrics["failure_recall"] == 0.5
    assert metrics["leniency_rate"] == 0.5
    assert metrics["strictness_rate"] == 0.5


def test_bootstrap_reproducible():
    pairs = [(True, True), (False, False), (False, True), (True, False)]

    def metric(h, a):
        return metric_bundle(h, a)["agreement"]

    assert bootstrap_interval(pairs, metric, iterations=200, seed=7) == bootstrap_interval(
        pairs, metric, iterations=200, seed=7
    )


def test_analysis_by_source_and_taxonomy():
    cases = {
        f"c{i}": EvaluationCase(
            case_id=f"c{i}",
            user_message=f"m{i}",
            expected_intent="x",
            needs_clarification=False,
            source_type="banking77_standard",
            notes="x",
        )
        for i in range(4)
    }
    labels = [
        HumanLabel(
            model_id="m",
            case_id=f"c{i}",
            human_outcome=outcome,
            failure_category="wrong_intent" if outcome == "fail" else None,
        )
        for i, outcome in enumerate(["pass", "pass", "fail", "fail"])
    ]
    result = analyze_evaluator_trust(
        labels,
        {("m", "c0"): True, ("m", "c1"): False, ("m", "c2"): True, ("m", "c3"): False},
        cases,
        iterations=50,
    )
    assert result["overall"]["failure_recall"] == 0.5
    assert result["disagreement_taxonomy"]["evaluator_too_lenient"] == 1


def config():
    return {
        "version": "1",
        "minimum_human_cases": 30,
        "minimum_human_failures": 5,
        "minimum_agreement": 0.85,
        "minimum_failure_recall": 0.9,
        "maximum_leniency_rate": 0.1,
    }


def test_gate_insufficient_without_file(tmp_path):
    assert (
        evaluate_gate(None, config(), human_label_file=tmp_path / "missing.csv").decision
        == "INSUFFICIENT_EVIDENCE"
    )


def test_gate_pass_and_fail(tmp_path):
    labels = tmp_path / "labels.csv"
    labels.write_text("present")
    passing = {
        "n": 30,
        "human_failures": 10,
        "agreement": 0.9,
        "failure_recall": 0.9,
        "leniency_rate": 0.1,
    }
    failing = passing | {"failure_recall": 0.8, "leniency_rate": 0.2}
    assert evaluate_gate(passing, config(), human_label_file=labels).decision == "PASS"
    decision = evaluate_gate(failing, config(), human_label_file=labels)
    assert decision.decision == "FAIL"
    assert any("failure_recall" in reason for reason in decision.reasons)


def test_gate_small_failure_denominator_is_insufficient(tmp_path):
    labels = tmp_path / "labels.csv"
    labels.write_text("present")
    metrics = {
        "n": 30,
        "human_failures": 2,
        "agreement": 1,
        "failure_recall": 1,
        "leniency_rate": 0,
    }
    assert (
        evaluate_gate(metrics, config(), human_label_file=labels).decision
        == "INSUFFICIENT_EVIDENCE"
    )
