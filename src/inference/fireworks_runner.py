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


def _add_usage(left: TokenUsage, right: TokenUsage) -> TokenUsage:
    return TokenUsage(
        prompt_tokens=left.prompt_tokens + right.prompt_tokens,
        completion_tokens=left.completion_tokens + right.completion_tokens,
        total_tokens=left.total_tokens + right.total_tokens,
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
    last_raw: str | None = None
    cumulative_usage = TokenUsage()
    for attempt in range(1, max_attempts + 1):
        try:
            response = await asyncio.wait_for(request(case), timeout=timeout_seconds)
            cumulative_usage = _add_usage(cumulative_usage, _usage(response))
            raw = response.choices[0].message.content
            last_raw = raw if isinstance(raw, str) else repr(raw)
            parsed = ModelPrediction.model_validate(json.loads(raw))
            cost = estimate_cost(cumulative_usage, *pricing) if pricing else None
            return RunRecord(
                case_id=case.case_id,
                model_id=model_id,
                started_at=started,
                completed_at=datetime.now(UTC),
                latency_ms=(time.perf_counter() - start_clock) * 1000,
                attempts=attempt,
                usage=cumulative_usage,
                estimated_cost_usd=cost,
                raw_response=raw,
                parsed_response=parsed,
            )
        except (
            TimeoutError,
            ConnectionError,
            OSError,
            RuntimeError,
            AttributeError,
            IndexError,
            KeyError,
            TypeError,
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
        usage=cumulative_usage,
        estimated_cost_usd=estimate_cost(cumulative_usage, *pricing) if pricing else None,
        raw_response=last_raw,
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


def load_recorded_spend(path: Path, model_id: str) -> float:
    """Sum persisted attempt costs so a resumed run cannot reset its budget."""
    if not path.exists():
        return 0.0
    spent = 0.0
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        record = RunRecord.model_validate_json(line)
        if record.model_id != model_id:
            continue
        if record.estimated_cost_usd is None:
            raise ValueError(
                f"line {line_number} has no estimated cost; cannot enforce a resumed hard cap"
            )
        spent += record.estimated_cost_usd
    return spent


async def run_dataset(
    cases: Iterable[EvaluationCase],
    model_id: str,
    output_path: Path,
    request: Callable[[EvaluationCase], Awaitable[Any]],
    *,
    max_concurrency: int = 5,
    hard_spend_cap_usd: float | None = None,
    maximum_cost_per_case_usd: float | None = None,
    **run_case_kwargs: Any,
) -> list[RunRecord]:
    if hard_spend_cap_usd is not None and (
        maximum_cost_per_case_usd is None or maximum_cost_per_case_usd <= 0
    ):
        raise ValueError(
            "maximum_cost_per_case_usd must be a positive, operator-confirmed retry-inclusive bound when a hard cap is enabled"
        )
    if hard_spend_cap_usd is not None and run_case_kwargs.get("pricing") is None:
        raise ValueError("pricing is required when a hard spend cap is enabled")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = load_completed(output_path, model_id)
    semaphore = asyncio.Semaphore(max_concurrency)

    async def bounded(case: EvaluationCase) -> RunRecord:
        async with semaphore:
            return await run_case(case, model_id, request, **run_case_kwargs)

    pending = [case for case in cases if case.case_id not in completed]
    records: list[RunRecord] = []
    spent = load_recorded_spend(output_path, model_id) if hard_spend_cap_usd is not None else 0.0
    start = 0
    while start < len(pending):
        batch_size = min(max_concurrency, len(pending) - start)
        if hard_spend_cap_usd is not None:
            assert maximum_cost_per_case_usd is not None
            remaining = hard_spend_cap_usd - spent
            affordable = int((remaining + 1e-12) // maximum_cost_per_case_usd)
            batch_size = min(batch_size, affordable)
            if batch_size < 1:
                raise RuntimeError(
                    "hard spend cap prevents another request: "
                    f"${spent:.6f} recorded, ${remaining:.6f} remaining, "
                    f"${maximum_cost_per_case_usd:.6f} reserved per case"
                )
        batch = pending[start : start + batch_size]
        for future in asyncio.as_completed([bounded(case) for case in batch]):
            record = await future
            with output_path.open("a", encoding="utf-8") as handle:
                handle.write(record.model_dump_json() + "\n")
            records.append(record)
            spent += record.estimated_cost_usd or 0.0
            if (
                maximum_cost_per_case_usd is not None
                and record.estimated_cost_usd is not None
                and record.estimated_cost_usd > maximum_cost_per_case_usd
            ):
                raise RuntimeError(
                    "actual retry-inclusive case cost exceeded maximum_cost_per_case_usd; "
                    "stop and correct the operator-provided bound"
                )
        start += batch_size
    return records
