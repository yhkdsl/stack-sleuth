import json
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from app.agent_loop import AgentLoop
from app.models import (
    FunctionCall,
    ModelTurn,
    ToolExecutionResult,
    ToolExecutionStatus,
    TraceStatus,
)
from app.trace_store import FileTraceStore


class FakeModelClient:
    def __init__(self, turns: Sequence[ModelTurn | Exception]) -> None:
        self.turns = list(turns)
        self.calls: list[dict[str, Any]] = []

    async def create(
        self,
        *,
        input_items: str | list[dict[str, Any]],
    ) -> ModelTurn:
        self.calls.append({"input_items": input_items})
        turn = self.turns.pop(0)
        if isinstance(turn, Exception):
            raise turn
        return turn


class FakeToolRouter:
    def __init__(self, results: Sequence[ToolExecutionResult]) -> None:
        self.results = list(results)
        self.calls: list[dict[str, Any]] = []

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        trace_id: str,
        request_id: str,
    ) -> ToolExecutionResult:
        self.calls.append(
            {
                "name": name,
                "arguments": arguments,
                "trace_id": trace_id,
                "request_id": request_id,
            }
        )
        return self.results.pop(0)


def turn(
    response_id: str,
    *,
    calls: list[FunctionCall] | None = None,
    text: str = "",
    tokens: int = 10,
    response_status: str = "completed",
    incomplete_reason: str | None = None,
    response_error_code: str | None = None,
) -> ModelTurn:
    resolved_calls = calls or []
    return ModelTurn(
        response_id=response_id,
        output_text=text,
        function_calls=resolved_calls,
        continuation_items=[
            {
                "type": "function_call",
                "call_id": call.call_id,
                "name": call.name,
                "arguments": call.arguments,
            }
            for call in resolved_calls
        ],
        usage={"inputTokens": tokens - 2, "outputTokens": 2, "totalTokens": tokens},
        response_status=response_status,
        incomplete_reason=incomplete_reason,
        response_error_code=response_error_code,
    )


async def test_agent_loop_runs_log_then_sql_then_returns_final_answer(tmp_path: Path) -> None:
    model = FakeModelClient(
        [
            turn(
                "resp-1",
                calls=[
                    FunctionCall(
                        call_id="call-logs",
                        name="search_error_logs",
                        arguments=json.dumps(
                            {"keyword": "ERROR", "sinceMinutes": 60, "limit": 20}
                        ),
                    )
                ],
            ),
            turn(
                "resp-2",
                calls=[
                    FunctionCall(
                        call_id="call-sql",
                        name="run_read_only_query",
                        arguments=json.dumps(
                            {
                                "sql": (
                                    "SELECT id, account_status, profile_img "
                                    "FROM users WHERE id = 42"
                                )
                            }
                        ),
                    )
                ],
            ),
            turn("resp-3", text="Three errors were caused by a null profile image."),
        ]
    )
    router = FakeToolRouter(
        [
            ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                output={"matchCount": 3, "matches": [{"message": "user_id=42"}]},
                latency_ms=4,
            ),
            ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                output={"rowCount": 1, "rows": [{"id": 42, "profile_img": None}]},
                latency_ms=6,
            ),
        ]
    )
    loop = AgentLoop(
        model_client=model,
        tool_router=router,
        trace_store=FileTraceStore(tmp_path),
        model="test-model",
        max_iterations=5,
        request_timeout_seconds=1,
    )

    trace = await loop.run("Investigate recent errors", trace_id="trace-happy")

    assert trace.status is TraceStatus.COMPLETED
    assert trace.finalAnswer == "Three errors were caused by a null profile image."
    assert trace.iterations == 3
    assert [call.name for call in trace.toolCalls] == [
        "search_error_logs",
        "run_read_only_query",
    ]
    assert trace.usage == {"inputTokens": 24, "outputTokens": 6, "totalTokens": 30}
    assert model.calls[1]["input_items"][0] == {
        "role": "user",
        "content": "Investigate recent errors",
    }
    assert model.calls[1]["input_items"][1]["type"] == "function_call"
    assert model.calls[1]["input_items"][2]["type"] == "function_call_output"
    assert model.calls[1]["input_items"][2]["call_id"] == "call-logs"
    assert await FileTraceStore(tmp_path).get("trace-happy") == trace


async def test_agent_loop_returns_structured_tool_error_to_model(tmp_path: Path) -> None:
    model = FakeModelClient(
        [
            turn(
                "resp-1",
                calls=[
                    FunctionCall(
                        call_id="call-sql",
                        name="run_read_only_query",
                        arguments='{"sql":"DELETE FROM users"}',
                    )
                ],
            ),
            turn("resp-2", text="The destructive query was blocked."),
        ]
    )
    router = FakeToolRouter(
        [
            ToolExecutionResult(
                status=ToolExecutionStatus.REJECTED,
                output={
                    "ok": False,
                    "status": "rejected",
                    "error": {"code": "SQL_WRITE_BLOCKED", "message": "Blocked."},
                },
                error_code="SQL_WRITE_BLOCKED",
                latency_ms=1,
            )
        ]
    )
    loop = AgentLoop(
        model_client=model,
        tool_router=router,
        trace_store=FileTraceStore(tmp_path),
        model="test-model",
        max_iterations=5,
        request_timeout_seconds=1,
    )

    trace = await loop.run("Delete users", trace_id="trace-rejected")

    output = json.loads(model.calls[1]["input_items"][2]["output"])
    assert output["error"]["code"] == "SQL_WRITE_BLOCKED"
    assert len(trace.guardrailRejections) == 1
    assert trace.guardrailRejections[0].status is ToolExecutionStatus.REJECTED


async def test_agent_loop_redacts_sensitive_tool_output_before_model_continuation(
    tmp_path: Path,
) -> None:
    model = FakeModelClient(
        [
            turn(
                "resp-1",
                calls=[
                    FunctionCall(
                        call_id="call-logs",
                        name="search_error_logs",
                        arguments='{"keyword":"ERROR","sinceMinutes":60,"limit":20}',
                    )
                ],
            ),
            turn("resp-2", text="Sensitive values were excluded from the analysis."),
        ]
    )
    router = FakeToolRouter(
        [
            ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                output={
                    "matches": [
                        {
                            "message": (
                                "ERROR contact=demo.user@example.test "
                                "Authorization=Bearer secret-token"
                            )
                        }
                    ]
                },
            )
        ]
    )
    loop = AgentLoop(
        model_client=model,
        tool_router=router,
        trace_store=FileTraceStore(tmp_path),
        model="test-model",
        max_iterations=2,
        request_timeout_seconds=1,
    )

    trace = await loop.run("Investigate", trace_id="trace-model-redaction")

    model_output = model.calls[1]["input_items"][2]["output"]
    persisted = (tmp_path / "trace-model-redaction.json").read_text()
    assert "demo.user@example.test" not in model_output
    assert "secret-token" not in model_output
    assert "demo.user@example.test" not in persisted
    assert "secret-token" not in persisted
    assert "[REDACTED]" in model_output
    assert trace.redactions


async def test_agent_loop_rejects_malformed_arguments_without_calling_router(
    tmp_path: Path,
) -> None:
    model = FakeModelClient(
        [
            turn(
                "resp-1",
                calls=[
                    FunctionCall(
                        call_id="call-bad",
                        name="search_error_logs",
                        arguments="{not-json",
                    )
                ],
            ),
            turn("resp-2", text="The tool request was invalid."),
        ]
    )
    router = FakeToolRouter([])
    loop = AgentLoop(
        model_client=model,
        tool_router=router,
        trace_store=FileTraceStore(tmp_path),
        model="test-model",
        max_iterations=5,
        request_timeout_seconds=1,
    )

    trace = await loop.run("Investigate", trace_id="trace-malformed")

    assert router.calls == []
    assert trace.toolResults[0].errorCode == "INVALID_TOOL_ARGUMENTS"
    assert trace.toolResults[0].status is ToolExecutionStatus.REJECTED


async def test_agent_loop_stops_after_max_iterations_and_persists_trace(
    tmp_path: Path,
) -> None:
    model = FakeModelClient(
        [
            turn(
                f"resp-{index}",
                calls=[
                    FunctionCall(
                        call_id=f"call-{index}",
                        name="check_server_health",
                        arguments='{"includeJvm":true,"includeDbPool":true}',
                    )
                ],
            )
            for index in range(2)
        ]
    )
    router = FakeToolRouter(
        [
            ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                output={"status": "ok"},
            )
            for _ in range(2)
        ]
    )
    store = FileTraceStore(tmp_path)
    loop = AgentLoop(
        model_client=model,
        tool_router=router,
        trace_store=store,
        model="test-model",
        max_iterations=2,
        request_timeout_seconds=1,
    )

    trace = await loop.run("Keep checking", trace_id="trace-max")

    assert trace.status is TraceStatus.INCOMPLETE
    assert trace.error == {
        "code": "MAX_ITERATIONS_REACHED",
        "message": "Agent stopped after 2 model iterations.",
    }
    assert (await store.get("trace-max")).status is TraceStatus.INCOMPLETE


async def test_agent_loop_marks_incomplete_model_response_without_empty_success(
    tmp_path: Path,
) -> None:
    model = FakeModelClient(
        [
            turn(
                "resp-incomplete",
                response_status="incomplete",
                incomplete_reason="max_output_tokens",
            )
        ]
    )
    loop = AgentLoop(
        model_client=model,
        tool_router=FakeToolRouter([]),
        trace_store=FileTraceStore(tmp_path),
        model="test-model",
        max_iterations=2,
        request_timeout_seconds=1,
    )

    trace = await loop.run("Investigate", trace_id="trace-model-incomplete")

    assert trace.status is TraceStatus.INCOMPLETE
    assert trace.finalAnswer is None
    assert trace.error == {
        "code": "MODEL_RESPONSE_INCOMPLETE",
        "message": "The model response was incomplete: max_output_tokens.",
    }


async def test_agent_loop_marks_failed_model_response_without_empty_success(
    tmp_path: Path,
) -> None:
    model = FakeModelClient(
        [
            turn(
                "resp-failed",
                response_status="failed",
                response_error_code="server_error",
            )
        ]
    )
    loop = AgentLoop(
        model_client=model,
        tool_router=FakeToolRouter([]),
        trace_store=FileTraceStore(tmp_path),
        model="test-model",
        max_iterations=2,
        request_timeout_seconds=1,
    )

    trace = await loop.run("Investigate", trace_id="trace-model-failed")

    assert trace.status is TraceStatus.FAILED
    assert trace.finalAnswer is None
    assert trace.error == {
        "code": "MODEL_RESPONSE_FAILED",
        "message": "The model returned a failed response.",
    }


async def test_agent_loop_rejects_completed_response_with_empty_final_answer(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(
        model_client=FakeModelClient([turn("resp-empty")]),
        tool_router=FakeToolRouter([]),
        trace_store=FileTraceStore(tmp_path),
        model="test-model",
        max_iterations=2,
        request_timeout_seconds=1,
    )

    trace = await loop.run("Investigate", trace_id="trace-empty-answer")

    assert trace.status is TraceStatus.INCOMPLETE
    assert trace.finalAnswer is None
    assert trace.error == {
        "code": "EMPTY_MODEL_OUTPUT",
        "message": "The model returned no tool call or final answer.",
    }


async def test_agent_loop_persists_openai_failure_without_leaking_message(
    tmp_path: Path,
) -> None:
    model = FakeModelClient([RuntimeError("Bearer secret-access-token")])
    loop = AgentLoop(
        model_client=model,
        tool_router=FakeToolRouter([]),
        trace_store=FileTraceStore(tmp_path),
        model="test-model",
        max_iterations=2,
        request_timeout_seconds=1,
    )

    trace = await loop.run("Investigate", trace_id="trace-model-failure")

    assert trace.status is TraceStatus.FAILED
    assert trace.error == {
        "code": "MODEL_ERROR",
        "message": "OpenAI request failed.",
    }
    assert "secret-access-token" not in (
        tmp_path / "trace-model-failure.json"
    ).read_text()


async def test_agent_loop_distinguishes_unexpected_execution_failure(
    tmp_path: Path,
) -> None:
    class BrokenRouter:
        async def execute(self, *_: Any, **__: Any) -> ToolExecutionResult:
            raise RuntimeError("database-password-should-not-leak")

    model = FakeModelClient(
        [
            turn(
                "resp-1",
                calls=[
                    FunctionCall(
                        call_id="call-health",
                        name="check_server_health",
                        arguments='{"includeJvm":true,"includeDbPool":true}',
                    )
                ],
            )
        ]
    )
    loop = AgentLoop(
        model_client=model,
        tool_router=BrokenRouter(),
        trace_store=FileTraceStore(tmp_path),
        model="test-model",
        max_iterations=2,
        request_timeout_seconds=1,
    )

    trace = await loop.run("Investigate", trace_id="trace-agent-failure")

    assert trace.status is TraceStatus.FAILED
    assert trace.error == {
        "code": "AGENT_EXECUTION_ERROR",
        "message": "Agent execution failed.",
    }
    assert "database-password-should-not-leak" not in (
        tmp_path / "trace-agent-failure.json"
    ).read_text()


async def test_agent_loop_enforces_total_request_timeout(tmp_path: Path) -> None:
    class SlowModel:
        async def create(self, **_: Any) -> ModelTurn:
            import asyncio

            await asyncio.sleep(0.05)
            return turn("late", text="Too late")

    loop = AgentLoop(
        model_client=SlowModel(),
        tool_router=FakeToolRouter([]),
        trace_store=FileTraceStore(tmp_path),
        model="test-model",
        max_iterations=2,
        request_timeout_seconds=0.01,
    )

    trace = await loop.run("Investigate", trace_id="trace-timeout")

    assert trace.status is TraceStatus.INCOMPLETE
    assert trace.error == {
        "code": "REQUEST_TIMEOUT",
        "message": "Agent request exceeded 0.01 seconds.",
    }


async def test_agent_loop_includes_trace_persistence_in_total_deadline(
    tmp_path: Path,
) -> None:
    class SlowTraceStore(FileTraceStore):
        def _write_temporary(self, trace: Any) -> Path:
            time.sleep(0.05)
            return super()._write_temporary(trace)

    loop = AgentLoop(
        model_client=FakeModelClient([turn("resp-1", text="All clear.")]),
        tool_router=FakeToolRouter([]),
        trace_store=SlowTraceStore(tmp_path),
        model="test-model",
        max_iterations=2,
        request_timeout_seconds=0.02,
    )

    started = time.perf_counter()
    trace = await loop.run("Investigate", trace_id="trace-slow-persistence")
    elapsed = time.perf_counter() - started

    assert elapsed < 0.04
    assert trace.status is TraceStatus.INCOMPLETE
    assert trace.error == {
        "code": "TRACE_PERSISTENCE_TIMEOUT",
        "message": "Trace persistence exceeded the total request deadline.",
    }
    import asyncio

    await asyncio.sleep(0.06)
    assert not (tmp_path / "trace-slow-persistence.json").exists()
    assert list(tmp_path.glob(".trace-slow-persistence.*.tmp")) == []
