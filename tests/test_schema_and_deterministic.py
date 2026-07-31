import pytest
from pydantic import ValidationError

from src.evaluators.deterministic import evaluate_prediction
from src.schemas import EvaluationCase, ModelPrediction


def test_case_ground_truth_consistency():
    with pytest.raises(ValidationError):
        EvaluationCase(
            case_id="bad",
            user_message="x",
            expected_intent="card_arrival",
            needs_clarification=True,
            source_type="authored_ambiguous",
            notes="x",
        )


def test_prediction_rejects_out_of_range_confidence():
    with pytest.raises(ValidationError):
        ModelPrediction(
            predicted_intent="card_arrival",
            confidence=1.1,
            needs_clarification=False,
            rationale="x",
        )


def test_exact_intent_passes(answerable_case):
    result = evaluate_prediction(
        answerable_case,
        '{"predicted_intent":"card_arrival","confidence":0.9,"needs_clarification":false,"rationale":"delivery question"}',
    )
    assert result.passed and result.intent_correct and result.schema_valid


def test_wrong_intent_has_explicit_reason(answerable_case):
    result = evaluate_prediction(
        answerable_case,
        {
            "predicted_intent": "cash_withdrawal",
            "confidence": 0.8,
            "needs_clarification": False,
            "rationale": "wrong",
        },
    )
    assert not result.passed
    assert result.failure_reasons == ["intent_mismatch: expected card_arrival, got cash_withdrawal"]


def test_ambiguous_case_requires_clarification(ambiguous_case):
    good = evaluate_prediction(
        ambiguous_case,
        {
            "predicted_intent": None,
            "confidence": 0.4,
            "needs_clarification": True,
            "rationale": "channel missing",
        },
    )
    bad = evaluate_prediction(
        ambiguous_case,
        {
            "predicted_intent": "cash_withdrawal_charge",
            "confidence": 0.7,
            "needs_clarification": False,
            "rationale": "guessed",
        },
    )
    assert good.passed
    assert not bad.passed and "clarification_mismatch" in bad.failure_reasons[0]


def test_parse_error_is_failure_not_pass(answerable_case):
    result = evaluate_prediction(answerable_case, "not json")
    assert not result.passed and not result.schema_valid
    assert result.failure_reasons[0].startswith("schema_invalid")
