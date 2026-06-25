from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.openai_client import OpenAIResponsesClient
from app.tool_schemas import TOOL_SCHEMAS


async def test_openai_adapter_uses_responses_api_contract() -> None:
    response = SimpleNamespace(
        id="resp-1",
        output=[
            SimpleNamespace(
                type="function_call",
                call_id="call-1",
                name="check_server_health",
                arguments='{"includeJvm":true,"includeDbPool":true}',
            )
        ],
        output_text="",
        usage=SimpleNamespace(input_tokens=8, output_tokens=2, total_tokens=10),
    )
    sdk = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(return_value=response)))
    adapter = OpenAIResponsesClient(sdk=sdk, model="test-model")

    turn = await adapter.create(
        input_items="Check health",
    )

    sdk.responses.create.assert_awaited_once_with(
        model="test-model",
        instructions=adapter.instructions,
        input="Check health",
        include=["reasoning.encrypted_content"],
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
        parallel_tool_calls=False,
        max_tool_calls=1,
        store=False,
    )
    assert turn.response_id == "resp-1"
    assert turn.function_calls[0].call_id == "call-1"
    assert turn.continuation_items[0]["type"] == "function_call"
    assert turn.usage == {"inputTokens": 8, "outputTokens": 2, "totalTokens": 10}
