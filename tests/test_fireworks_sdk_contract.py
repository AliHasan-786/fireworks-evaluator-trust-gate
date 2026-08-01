import inspect
import json

import httpx
import pytest
from fireworks import AsyncFireworks

from src.inference.fireworks_runner import create_fireworks_request


@pytest.mark.asyncio
async def test_production_request_uses_real_async_sdk_contract(answerable_case):
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        payload = json.loads(request.content)
        assert "card_arrival" in payload["messages"][0]["content"]
        return httpx.Response(
            200,
            json={
                "id": "contract-test",
                "object": "chat.completion",
                "created": 1,
                "model": "accounts/fireworks/models/gpt-oss-20b",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(
                                {
                                    "predicted_intent": "card_arrival",
                                    "confidence": 0.9,
                                    "needs_clarification": False,
                                    "rationale": "delivery question",
                                }
                            ),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 10,
                    "total_tokens": 20,
                },
            },
        )

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = AsyncFireworks(api_key="dummy", http_client=http_client)
    try:
        request = create_fireworks_request(
            client,
            "accounts/fireworks/models/gpt-oss-20b",
            answerable_case,
            320,
            ["card_arrival"],
        )
        assert inspect.isawaitable(request)
        response = await request
        assert response.choices[0].message.content
    finally:
        await client.close()
