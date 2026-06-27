from pathlib import Path
from typing import Any

import httpx

from app.config import Settings
from app.main import create_app
from app.models import AgentTrace, TraceStatus
from app.trace_store import FileTraceStore


def trace(status: TraceStatus = TraceStatus.COMPLETED) -> AgentTrace:
    error = None
    if status is TraceStatus.INCOMPLETE:
        error = {
            "code": "REQUEST_TIMEOUT",
            "message": "Agent execution exhausted its 27 second budget.",
        }
    return AgentTrace(
        traceId="trace_api_123",
        status=status,
        startedAt="2026-06-25T00:00:00Z",
        completedAt="2026-06-25T00:00:01Z",
        userRequest="Investigate",
        model="test-model",
        iterations=1,
        toolCalls=[],
        toolResults=[],
        guardrailRejections=[],
        redactions=[],
        usage={"inputTokens": 8, "outputTokens": 2, "totalTokens": 10},
        estimatedCost=None,
        pricingMetadata=None,
        totalDurationMs=1000,
        confidence=None,
        finalAnswer="All clear" if status is TraceStatus.COMPLETED else None,
        error=error,
    )


class FakeLoop:
    def __init__(self, result: AgentTrace) -> None:
        self.result = result
        self.requests: list[str] = []

    async def run(self, user_request: str, *, trace_id: str | None = None) -> AgentTrace:
        self.requests.append(user_request)
        return self.result


def settings(tmp_path: Path) -> Settings:
    return Settings(
        openai_api_key=None,
        agent_model="test-model",
        trace_directory=tmp_path,
        cors_origins=["http://localhost:3000"],
    )


async def request(app: Any, method: str, path: str, **kwargs: Any) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


async def test_run_endpoint_returns_completed_trace(tmp_path: Path) -> None:
    loop = FakeLoop(trace())
    app = create_app(settings(tmp_path), agent_loop=loop)

    response = await request(
        app,
        "POST",
        "/agent/run",
        json={"request": "Investigate recent errors"},
    )

    assert response.status_code == 200
    assert response.json()["traceId"] == "trace_api_123"
    assert response.json()["finalAnswer"] == "All clear"
    assert loop.requests == ["Investigate recent errors"]


async def test_run_endpoint_returns_gateway_timeout_with_trace_id(tmp_path: Path) -> None:
    app = create_app(
        settings(tmp_path),
        agent_loop=FakeLoop(trace(TraceStatus.INCOMPLETE)),
    )

    response = await request(
        app,
        "POST",
        "/agent/run",
        json={"request": "Investigate"},
    )

    assert response.status_code == 504
    assert response.json()["traceId"] == "trace_api_123"
    assert response.json()["error"]["code"] == "REQUEST_TIMEOUT"


async def test_trace_endpoint_replays_persisted_trace(tmp_path: Path) -> None:
    store = FileTraceStore(tmp_path)
    await store.save(trace())
    app = create_app(settings(tmp_path), trace_store=store)

    response = await request(app, "GET", "/agent/traces/trace_api_123")

    assert response.status_code == 200
    assert response.json()["traceId"] == "trace_api_123"


async def test_trace_endpoint_returns_structured_not_found(tmp_path: Path) -> None:
    app = create_app(settings(tmp_path))

    response = await request(app, "GET", "/agent/traces/trace_missing")

    assert response.status_code == 404
    assert response.json() == {
        "code": "TRACE_NOT_FOUND",
        "message": "Trace was not found.",
    }


async def test_run_requires_non_blank_request(tmp_path: Path) -> None:
    app = create_app(settings(tmp_path), agent_loop=FakeLoop(trace()))

    response = await request(app, "POST", "/agent/run", json={"request": "   "})

    assert response.status_code == 422


async def test_run_rejects_request_larger_than_configured_limit(
    tmp_path: Path,
) -> None:
    limited_settings = Settings(
        openai_api_key=None,
        agent_model="test-model",
        trace_directory=tmp_path,
        cors_origins=["http://localhost:3000"],
        max_user_request_chars=10,
    )
    loop = FakeLoop(trace())
    app = create_app(limited_settings, agent_loop=loop)

    response = await request(
        app,
        "POST",
        "/agent/run",
        json={"request": "x" * 11},
    )

    assert response.status_code == 413
    assert response.json() == {
        "code": "REQUEST_TOO_LARGE",
        "message": "Agent request exceeds the 10 character limit.",
    }
    assert loop.requests == []


async def test_live_run_without_api_key_returns_safe_configuration_error(
    tmp_path: Path,
) -> None:
    app = create_app(settings(tmp_path))

    response = await request(
        app,
        "POST",
        "/agent/run",
        json={"request": "Investigate"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "code": "AGENT_NOT_CONFIGURED",
        "message": "Set OPENAI_API_KEY and AGENT_MODEL to enable live agent runs.",
    }


async def test_cors_allows_only_configured_dashboard_origin(tmp_path: Path) -> None:
    app = create_app(settings(tmp_path), agent_loop=FakeLoop(trace()))

    response = await request(
        app,
        "OPTIONS",
        "/agent/run",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
