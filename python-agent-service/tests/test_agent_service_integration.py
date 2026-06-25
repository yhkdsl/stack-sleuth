import json
from pathlib import Path
from typing import Any

import httpx
import respx

from app.agent_loop import AgentLoop
from app.config import Settings
from app.main import create_app
from app.models import FunctionCall, ModelTurn
from app.tool_router import SpringToolRouter
from app.trace_store import FileTraceStore


class ScriptedModelClient:
    def __init__(self) -> None:
        self.turn = 0

    async def create(
        self,
        *,
        input_items: str | list[dict[str, Any]],
    ) -> ModelTurn:
        self.turn += 1
        if self.turn == 1:
            arguments = json.dumps(
                {"keyword": "ERROR", "sinceMinutes": 60, "limit": 20}
            )
            return ModelTurn(
                response_id="resp-integration-1",
                output_text="",
                function_calls=[
                    FunctionCall(
                        call_id="call-integration-logs",
                        name="search_error_logs",
                        arguments=arguments,
                    )
                ],
                continuation_items=[
                    {
                        "type": "function_call",
                        "call_id": "call-integration-logs",
                        "name": "search_error_logs",
                        "arguments": arguments,
                    }
                ],
                usage={"inputTokens": 12, "outputTokens": 4, "totalTokens": 16},
            )
        return ModelTurn(
            response_id="resp-integration-2",
            output_text="Three errors reference synthetic user 42.",
            function_calls=[],
            continuation_items=[{"type": "message", "role": "assistant"}],
            usage={"inputTokens": 20, "outputTokens": 8, "totalTokens": 28},
        )


def settings(tmp_path: Path) -> Settings:
    return Settings(
        openai_api_key=None,
        agent_model="integration-model",
        trace_directory=tmp_path,
        cors_origins=["http://localhost:3000"],
    )


@respx.mock
async def test_http_run_routes_tool_call_and_replays_redacted_trace(
    tmp_path: Path,
) -> None:
    spring_route = respx.post(
        "http://tool-server:8080/internal/tools/logs/search"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "ok",
                "matchCount": 3,
                "matches": [
                    {
                        "requestId": "req-demo-4201",
                        "message": "ERROR user_id=42 contact=demo.user@example.test",
                    }
                ],
            },
        )
    )
    store = FileTraceStore(tmp_path)
    loop = AgentLoop(
        model_client=ScriptedModelClient(),
        tool_router=SpringToolRouter(
            base_url="http://tool-server:8080",
            token="integration-token",
            timeout_seconds=1,
            max_output_chars=8000,
        ),
        trace_store=store,
        model="integration-model",
        max_iterations=5,
        request_timeout_seconds=2,
    )
    app = create_app(settings(tmp_path), agent_loop=loop, trace_store=store)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://agent-service",
    ) as client:
        run_response = await client.post(
            "/agent/run",
            json={"request": "Investigate errors from the last hour"},
        )
        trace_id = run_response.json()["traceId"]
        replay_response = await client.get(f"/agent/traces/{trace_id}")

    assert run_response.status_code == 200
    assert replay_response.status_code == 200
    assert replay_response.json() == run_response.json()
    assert run_response.json()["toolResults"][0]["status"] == "success"
    assert "[REDACTED]" in run_response.json()["toolResults"][0]["output"]["matches"][0][
        "message"
    ]
    assert run_response.json()["redactions"]
    spring_request = spring_route.calls.last.request
    assert spring_request.headers["X-Tool-Server-Token"] == "integration-token"
    assert spring_request.headers["X-Trace-Id"] == trace_id
    assert spring_request.headers["X-Request-Id"].startswith("req_")
