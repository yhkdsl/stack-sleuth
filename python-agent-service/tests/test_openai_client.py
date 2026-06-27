from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.openai_client import OpenAIResponsesClient
from app.tool_schemas import TOOL_SCHEMAS


async def test_openai_adapter_uses_responses_api_contract() -> None:
    response = SimpleNamespace(
        id="resp-1",
        status="completed",
        incomplete_details=None,
        error=None,
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
    adapter = OpenAIResponsesClient(
        sdk=sdk,
        model="test-model",
        max_output_tokens=900,
    )

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
        max_output_tokens=900,
        store=False,
    )
    assert turn.response_id == "resp-1"
    assert turn.response_status == "completed"
    assert turn.incomplete_reason is None
    assert turn.response_error_code is None
    assert turn.function_calls[0].call_id == "call-1"
    assert turn.continuation_items[0]["type"] == "function_call"
    assert turn.usage == {"inputTokens": 8, "outputTokens": 2, "totalTokens": 10}


async def test_openai_adapter_preserves_incomplete_response_metadata() -> None:
    response = SimpleNamespace(
        id="resp-incomplete",
        status="incomplete",
        incomplete_details=SimpleNamespace(reason="max_output_tokens"),
        error=None,
        output=[],
        output_text="",
        usage=None,
    )
    sdk = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(return_value=response)))
    adapter = OpenAIResponsesClient(
        sdk=sdk,
        model="test-model",
        max_output_tokens=900,
    )

    turn = await adapter.create(input_items="Investigate")

    assert turn.response_status == "incomplete"
    assert turn.incomplete_reason == "max_output_tokens"
    assert turn.response_error_code is None


async def test_openai_adapter_preserves_failed_response_code() -> None:
    response = SimpleNamespace(
        id="resp-failed",
        status="failed",
        incomplete_details=None,
        error=SimpleNamespace(code="server_error", message="internal details"),
        output=[],
        output_text="",
        usage=None,
    )
    sdk = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(return_value=response)))
    adapter = OpenAIResponsesClient(
        sdk=sdk,
        model="test-model",
        max_output_tokens=900,
    )

    turn = await adapter.create(input_items="Investigate")

    assert turn.response_status == "failed"
    assert turn.incomplete_reason is None
    assert turn.response_error_code == "server_error"
