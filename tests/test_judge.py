import pytest

from src.evaluators.llm_judge import judge_rationale
from src.schemas import ModelPrediction


@pytest.mark.asyncio
async def test_judge_failure_is_separate(ambiguous_case):
    class Broken:
        async def judge(self, **_kwargs):
            raise TimeoutError

    prediction = ModelPrediction(
        predicted_intent=None, confidence=0.3, needs_clarification=True, rationale="maybe a fee"
    )
    result = await judge_rationale(Broken(), ambiguous_case, prediction)
    assert not result.judge_succeeded
    assert result.error_type == "TimeoutError"


@pytest.mark.asyncio
async def test_judge_structured_result(ambiguous_case):
    class Good:
        async def judge(self, **_kwargs):
            return '{"rationale_identifies_real_ambiguity":true,"rationale_score":1,"reason":"Names the missing channel."}'

    prediction = ModelPrediction(
        predicted_intent=None,
        confidence=0.3,
        needs_clarification=True,
        rationale="The payment channel is missing.",
    )
    result = await judge_rationale(Good(), ambiguous_case, prediction)
    assert result.judge_succeeded and result.rationale_score == 1
