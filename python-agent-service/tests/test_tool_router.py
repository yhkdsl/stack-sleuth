import httpx
import pytest
import respx

from app.models import ToolExecutionStatus
from app.tool_router import SpringToolRouter


@pytest.fixture
def router() -> SpringToolRouter:
    return SpringToolRouter(
        base_url="http://tool-server:8080",
        token="test-token",
        timeout_seconds=0.05,
        max_output_chars=120,
    )


@respx.mock
async def test_router_calls_expected_spring_endpoint_with_correlation_headers(
    router: SpringToolRouter,
) -> None:
    route = respx.post("http://tool-server:8080/internal/tools/logs/search").mock(
        return_value=httpx.Response(
            200,
            json={"status": "ok", "keyword": "ERROR", "matchCount": 0, "matches": []},
        )
    )

    result = await router.execute(
        "search_error_logs",
        {"keyword": "ERROR", "sinceMinutes": 60, "limit": 20},
        trace_id="trace-1",
        request_id="request-1",
    )

    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.output["matchCount"] == 0
    request = route.calls.last.request
    assert request.headers["X-Tool-Server-Token"] == "test-token"
    assert request.headers["X-Trace-Id"] == "trace-1"
    assert request.headers["X-Request-Id"] == "request-1"


@respx.mock
async def test_router_returns_structured_guardrail_rejection(
    router: SpringToolRouter,
) -> None:
    respx.post("http://tool-server:8080/internal/tools/sql/read-only").mock(
        return_value=httpx.Response(
            400,
            json={
                "code": "SQL_WRITE_BLOCKED",
                "message": "Only SELECT statements are allowed.",
                "fieldErrors": [],
            },
        )
    )

    result = await router.execute(
        "run_read_only_query",
        {"sql": "DELETE FROM users"},
        trace_id="trace-1",
        request_id="request-2",
    )

    assert result.status is ToolExecutionStatus.REJECTED
    assert result.error_code == "SQL_WRITE_BLOCKED"
    assert result.output == {
        "ok": False,
        "status": "rejected",
        "error": {
            "code": "SQL_WRITE_BLOCKED",
            "message": "Only SELECT statements are allowed.",
        },
    }


async def test_router_rejects_unknown_tool_without_http_call(
    router: SpringToolRouter,
) -> None:
    result = await router.execute(
        "run_shell",
        {"command": "whoami"},
        trace_id="trace-1",
        request_id="request-3",
    )

    assert result.status is ToolExecutionStatus.REJECTED
    assert result.error_code == "TOOL_NOT_ALLOWED"


@respx.mock
async def test_router_marks_timeout_as_structured_failure(router: SpringToolRouter) -> None:
    async def timeout(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    respx.post("http://tool-server:8080/internal/tools/health").mock(side_effect=timeout)

    result = await router.execute(
        "check_server_health",
        {"includeJvm": True, "includeDbPool": True},
        trace_id="trace-1",
        request_id="request-4",
    )

    assert result.status is ToolExecutionStatus.TIMED_OUT
    assert result.error_code == "TOOL_TIMEOUT"
    assert "0.05" in result.output["error"]["message"]


@respx.mock
async def test_router_truncates_large_tool_output_as_valid_json(
    router: SpringToolRouter,
) -> None:
    respx.post("http://tool-server:8080/internal/tools/logs/search").mock(
        return_value=httpx.Response(200, json={"status": "ok", "matches": ["x" * 500]})
    )

    result = await router.execute(
        "search_error_logs",
        {"keyword": "ERROR", "sinceMinutes": 60, "limit": 20},
        trace_id="trace-1",
        request_id="request-5",
    )

    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.output["truncated"] is True
    assert len(result.output["content"]) == 120


@respx.mock
async def test_router_structures_non_object_spring_response(
    router: SpringToolRouter,
) -> None:
    respx.post("http://tool-server:8080/internal/tools/health").mock(
        return_value=httpx.Response(502, json=["unexpected"])
    )

    result = await router.execute(
        "check_server_health",
        {"includeJvm": True, "includeDbPool": True},
        trace_id="trace-1",
        request_id="request-6",
    )

    assert result.status is ToolExecutionStatus.FAILED
    assert result.error_code == "TOOL_INVALID_RESPONSE"
    assert result.output["error"]["message"] == (
        "Tool server returned a non-object JSON response."
    )
