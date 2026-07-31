import json
from types import SimpleNamespace

import pytest

from src.inference.fireworks_runner import estimate_cost, load_completed, run_case, run_dataset
from src.schemas import TokenUsage


def response(content: str):
    usage = SimpleNamespace(prompt_tokens=100, completion_tokens=20, total_tokens=120)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))], usage=usage
    )


def valid_content():
    return json.dumps(
        {
            "predicted_intent": "card_arrival",
            "confidence": 0.9,
            "needs_clarification": False,
            "rationale": "delivery",
        }
    )


def test_cost_calculation():
    assert (
        estimate_cost(TokenUsage(prompt_tokens=1_000_000, completion_tokens=500_000), 0.9, 1.8)
        == 1.8
    )


@pytest.mark.asyncio
async def test_retry_limit_and_success(answerable_case):
    calls = 0

    async def request(_case):
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError("temporary")
        return response(valid_content())

    async def no_sleep(_seconds):
        return None

    record = await run_case(
        answerable_case, "model", request, max_attempts=3, sleep=no_sleep, pricing=(0.9, 1.8)
    )
    assert calls == 3 and record.parsed_response is not None and record.attempts == 3


@pytest.mark.asyncio
async def test_errors_never_become_predictions(answerable_case):
    async def request(_case):
        raise RuntimeError("down")

    async def no_sleep(_seconds):
        return None

    record = await run_case(answerable_case, "model", request, max_attempts=2, sleep=no_sleep)
    assert (
        record.parsed_response is None
        and record.error_type == "RuntimeError"
        and record.attempts == 2
    )


@pytest.mark.asyncio
async def test_resumability_skips_completed(tmp_path, answerable_case):
    calls = 0

    async def request(_case):
        nonlocal calls
        calls += 1
        return response(valid_content())

    path = tmp_path / "runs.jsonl"
    await run_dataset([answerable_case], "model", path, request)
    await run_dataset([answerable_case], "model", path, request)
    assert calls == 1
    assert load_completed(path, "model") == {answerable_case.case_id}
