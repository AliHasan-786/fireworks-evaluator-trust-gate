from __future__ import annotations

import asyncio
import json
import random
import time
from collections.abc import Awaitable, Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.schemas import EvaluationCase, ModelPrediction, RunRecord, TokenUsage

SYSTEM_PROMPT = """You route banking support messages. Choose exactly one Banking77 intent when the request is answerable. If multiple intents are plausible or key information is missing, set needs_clarification=true and predicted_intent=null. Return JSON matching the schema. Keep rationale under 80 words."""


def estimate_cost(usage: TokenUsage, input_per_million: float, output_per_million: float) -> float:
    return round(
        usage.prompt_tokens * input_per_million / 1_000_000
        + usage.completion_tokens * output_per_million / 1_000_000,
        10,
    )


def _usage(response: Any) -> TokenUsage:
    usage = getattr(response, "usage", None)
    if usage is None:
        return TokenUsage()
    return TokenUsage(
        prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
        completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
        total_tokens=int(getattr(usage, "total_tokens", 0) or 0),
    )


def create_fireworks_request(
    client: Any, model_id: str, case: EvaluationCase, max_tokens: int
) -> Awaitable[Any]:
    schema = ModelPrediction.model_json_schema()
    return client.chat.completions.acreate(
        model=model_id,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": case.user_message},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "routing_decision", "schema": schema},
        },
        temperature=0,
        max_tokens=max_tokens,
    )


async def run_case(
    case: EvaluationCase,
    model_id: str,
    request: Callable[[EvaluationCase], Awaitable[Any]],
    *,
    max_attempts: int = 3,
    timeout_seconds: float = 45,
    base_backoff_seconds: float = 1,
    pricing: tuple[float, float] | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> RunRecord:
    started = datetime.now(UTC)
    start_clock = time.perf_counter()
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = await asyncio.wait_for(request(case), timeout=timeout_seconds)
            raw = response.choices[0].message.content
            parsed = ModelPrediction.model_validate(json.loads(raw))
            usage = _usage(response)
            cost = estimate_cost(usage, *pricing) if pricing else None
            return RunRecord(
                case_id=case.case_id,
                model_id=model_id,
                started_at=started,
                completed_at=datetime.now(UTC),
                latency_ms=(time.perf_counter() - start_clock) * 1000,
                attempts=attempt,
                usage=usage,
                estimated_cost_usd=cost,
                raw_response=raw,
                parsed_response=parsed,
            )
        except (
            TimeoutError,
            ConnectionError,
            OSError,
            RuntimeError,
            json.JSONDecodeError,
            ValidationError,
        ) as exc:
            last_exc = exc
            if attempt < max_attempts:
                await sleep(
                    base_backoff_seconds * (2 ** (attempt - 1)) * (0.8 + random.random() * 0.4)
                )
    assert last_exc is not None
    return RunRecord(
        case_id=case.case_id,
        model_id=model_id,
        started_at=started,
        completed_at=datetime.now(UTC),
        latency_ms=(time.perf_counter() - start_clock) * 1000,
        attempts=max_attempts,
        error_type=type(last_exc).__name__,
        error_message=str(last_exc),
    )


def load_completed(path: Path, model_id: str) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    for line in path.read_text().splitlines():
        if line.strip():
            record = RunRecord.model_validate_json(line)
            if record.model_id == model_id and record.parsed_response is not None:
                completed.add(record.case_id)
    return completed


async def run_dataset(
    cases: Iterable[EvaluationCase],
    model_id: str,
    output_path: Path,
    request: Callable[[EvaluationCase], Awaitable[Any]],
    *,
    max_concurrency: int = 5,
    hard_spend_cap_usd: float | None = None,
    **run_case_kwargs: Any,
) -> list[RunRecord]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = load_completed(output_path, model_id)
    semaphore = asyncio.Semaphore(max_concurrency)

    async def bounded(case: EvaluationCase) -> RunRecord:
        async with semaphore:
            return await run_case(case, model_id, request, **run_case_kwargs)

    pending = [case for case in cases if case.case_id not in completed]
    records: list[RunRecord] = []
    spent = 0.0
    for start in range(0, len(pending), max_concurrency):
        batch = pending[start : start + max_concurrency]
        for future in asyncio.as_completed([bounded(case) for case in batch]):
            record = await future
            with output_path.open("a", encoding="utf-8") as handle:
                handle.write(record.model_dump_json() + "\n")
            records.append(record)
            spent += record.estimated_cost_usd or 0.0
        if hard_spend_cap_usd is not None and spent >= hard_spend_cap_usd:
            raise RuntimeError(
                f"hard spend cap reached after a bounded batch: ${spent:.6f} >= ${hard_spend_cap_usd:.2f}"
            )
    return records
