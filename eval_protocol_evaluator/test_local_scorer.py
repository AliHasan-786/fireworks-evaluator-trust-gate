from evaluator import score


def test_exact_answerable_passes():
    case = {"expected_intent": "card_arrival", "needs_clarification": False}
    content = '{"predicted_intent":"card_arrival","confidence":0.9,"needs_clarification":false,"rationale":"The user asks where the card is."}'
    assert score(case, content)[0] == 1.0


def test_ambiguous_forced_intent_fails():
    case = {"expected_intent": None, "needs_clarification": True}
    content = '{"predicted_intent":"cash_withdrawal_charge","confidence":0.4,"needs_clarification":false,"rationale":"A fee is possible."}'
    assert score(case, content) == (0.0, "clarification_mismatch")
