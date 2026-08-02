from __future__ import annotations

import json
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.schemas import EvaluationCase, JudgeResult, ModelPrediction

RUBRIC = """Assess only whether the rationale identifies the material ambiguity or missing information in the user message. Do not re-grade intent correctness, schema validity, confidence, or the clarification decision. Score 1 only if the rationale names the conflicting plausible intents or the specific information needed to route safely; otherwise score 0. Return strict JSON."""


class JudgePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rationale_identifies_real_ambiguity: bool
    rationale_score: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)


class JudgeClient(Protocol):
    async def judge(self, *, prompt: str, schema: dict[str, Any]) -> str: ...


class FireworksJudgeClient:
    def __init__(self, client: Any, model_id: str, timeout_seconds: float = 45):
        self.client = client
        self.model_id = model_id
        self.timeout_seconds = timeout_seconds

    async def judge(self, *, prompt: str, schema: dict[str, Any]) -> str:
        import asyncio

        response = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "rationale_judgment", "schema": schema},
                },
                temperature=0,
                max_tokens=220,
            ),
            timeout=self.timeout_seconds,
        )
        return response.choices[0].message.content


def build_judge_prompt(case: EvaluationCase, prediction: ModelPrediction) -> str:
    return (
        f"{RUBRIC}\n\nUser message: {case.user_message}\n"
        f"Ground-truth note: {case.notes}\nModel rationale: {prediction.rationale}\n"
        "Return JSON matching the provided schema."
    )


async def judge_rationale(
    client: JudgeClient, case: EvaluationCase, prediction: ModelPrediction
) -> JudgeResult:
    if not case.needs_clarification:
        return JudgeResult(judge_succeeded=True, reason="not applicable to answerable case")
    try:
        raw = await client.judge(
            prompt=build_judge_prompt(case, prediction), schema=JudgePayload.model_json_schema()
        )
        parsed = JudgePayload.model_validate(json.loads(raw))
        return JudgeResult(judge_succeeded=True, **parsed.model_dump())
    except (ValidationError, json.JSONDecodeError, TimeoutError, RuntimeError, ValueError) as exc:
        return JudgeResult(
            judge_succeeded=False,
            reason="judge failure; model result remains unchanged",
            error_type=type(exc).__name__,
        )
