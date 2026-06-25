import asyncio
import json
import time
import uuid
from datetime import UTC, datetime
from typing import Any, Protocol

from app.models import (
    AgentTrace,
    ModelTurn,
    RedactionEvent,
    ToolCallRecord,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolResultRecord,
    TraceStatus,
)
from app.redaction import redact
from app.trace_store import FileTraceStore

_MAX_TRACE_PERSISTENCE_RESERVE_SECONDS = 0.1


class ModelClient(Protocol):
    async def create(
        self,
        *,
        input_items: str | list[dict[str, Any]],
    ) -> ModelTurn: ...


class ToolRouter(Protocol):
    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        trace_id: str,
        request_id: str,
    ) -> ToolExecutionResult: ...


class ModelCallError(Exception):
    pass


class AgentLoop:
    def __init__(
        self,
        *,
        model_client: ModelClient,
        tool_router: ToolRouter,
        trace_store: FileTraceStore,
        model: str,
        max_iterations: int,
        request_timeout_seconds: float,
    ) -> None:
        self._model_client = model_client
        self._tool_router = tool_router
        self._trace_store = trace_store
        self._model = model
        self._max_iterations = max_iterations
        self._request_timeout_seconds = request_timeout_seconds

    async def run(self, user_request: str, *, trace_id: str | None = None) -> AgentTrace:
        trace = AgentTrace(
            traceId=trace_id or f"trace_{uuid.uuid4().hex}",
            status=TraceStatus.RUNNING,
            startedAt=_now(),
            completedAt=None,
            userRequest=user_request,
            model=self._model,
            iterations=0,
            toolCalls=[],
            toolResults=[],
            guardrailRejections=[],
            redactions=[],
            usage={"inputTokens": 0, "outputTokens": 0, "totalTokens": 0},
            estimatedCost=None,
            pricingMetadata=None,
            totalDurationMs=None,
            confidence=None,
            finalAnswer=None,
        )
        started = time.perf_counter()
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._request_timeout_seconds
        persistence_reserve = min(
            _MAX_TRACE_PERSISTENCE_RESERVE_SECONDS,
            self._request_timeout_seconds * 0.1,
        )
        execution_timeout = self._request_timeout_seconds - persistence_reserve
        try:
            async with asyncio.timeout(execution_timeout):
                await self._run_iterations(trace)
        except TimeoutError:
            trace.status = TraceStatus.INCOMPLETE
            trace.error = {
                "code": "REQUEST_TIMEOUT",
                "message": (
                    f"Agent request exceeded {self._request_timeout_seconds:g} seconds."
                ),
            }
        except ModelCallError:
            trace.status = TraceStatus.FAILED
            trace.error = {
                "code": "MODEL_ERROR",
                "message": "OpenAI request failed.",
            }
        except Exception:
            trace.status = TraceStatus.FAILED
            trace.error = {
                "code": "AGENT_EXECUTION_ERROR",
                "message": "Agent execution failed.",
            }
        finally:
            trace.completedAt = _now()
            trace.totalDurationMs = round((time.perf_counter() - started) * 1000)

        remaining = deadline - loop.time()
        if remaining > 0:
            try:
                async with asyncio.timeout(remaining):
                    return await self._trace_store.save(trace)
            except TimeoutError:
                pass

        if trace.error is None:
            trace.status = TraceStatus.INCOMPLETE
            trace.finalAnswer = None
            trace.error = {
                "code": "TRACE_PERSISTENCE_TIMEOUT",
                "message": "Trace persistence exceeded the total request deadline.",
            }
        trace.completedAt = _now()
        trace.totalDurationMs = round((time.perf_counter() - started) * 1000)
        return self._trace_store.sanitize(trace)

    async def _run_iterations(self, trace: AgentTrace) -> None:
        input_items: list[dict[str, Any]] = [
            {"role": "user", "content": trace.userRequest}
        ]
        for iteration in range(1, self._max_iterations + 1):
            try:
                turn = await self._model_client.create(input_items=input_items)
            except Exception as exception:
                raise ModelCallError from exception
            trace.iterations = iteration
            _add_usage(trace.usage, turn.usage)

            if turn.response_status == "incomplete":
                reason = turn.incomplete_reason or "unknown_reason"
                trace.status = TraceStatus.INCOMPLETE
                trace.error = {
                    "code": "MODEL_RESPONSE_INCOMPLETE",
                    "message": f"The model response was incomplete: {reason}.",
                }
                return

            if turn.response_status != "completed":
                trace.status = TraceStatus.FAILED
                trace.error = {
                    "code": "MODEL_RESPONSE_FAILED",
                    "message": "The model returned a failed response.",
                }
                return

            if not turn.function_calls:
                if not turn.output_text.strip():
                    trace.status = TraceStatus.INCOMPLETE
                    trace.error = {
                        "code": "EMPTY_MODEL_OUTPUT",
                        "message": "The model returned no tool call or final answer.",
                    }
                    return
                trace.status = TraceStatus.COMPLETED
                trace.finalAnswer = turn.output_text
                return

            tool_outputs: list[dict[str, Any]] = []
            for call in turn.function_calls:
                request_id = f"req_{uuid.uuid4().hex}"
                result, arguments = await self._execute_call(
                    call.name,
                    call.arguments,
                    trace_id=trace.traceId,
                    request_id=request_id,
                )
                safe_output, redaction_events = redact(result.output)
                result.output = safe_output
                result_index = len(trace.toolResults)
                trace.redactions.extend(
                    RedactionEvent(
                        path=(
                            f"$.toolResults[{result_index}].output"
                            f"{event.path.removeprefix('$')}"
                        ),
                        reason=event.reason,
                    )
                    for event in redaction_events
                )
                call_record = ToolCallRecord(
                    callId=call.call_id,
                    requestId=request_id,
                    name=call.name,
                    arguments=arguments,
                    iteration=iteration,
                )
                result_record = ToolResultRecord(
                    callId=call.call_id,
                    requestId=request_id,
                    name=call.name,
                    status=result.status,
                    output=result.output,
                    errorCode=result.error_code,
                    latencyMs=result.latency_ms,
                )
                trace.toolCalls.append(call_record)
                trace.toolResults.append(result_record)
                if result.status is ToolExecutionStatus.REJECTED:
                    trace.guardrailRejections.append(result_record)
                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(
                            result.output,
                            ensure_ascii=True,
                            separators=(",", ":"),
                        ),
                    }
                )
            input_items = [*input_items, *turn.continuation_items, *tool_outputs]

        trace.status = TraceStatus.INCOMPLETE
        trace.error = {
            "code": "MAX_ITERATIONS_REACHED",
            "message": f"Agent stopped after {self._max_iterations} model iterations.",
        }

    async def _execute_call(
        self,
        name: str,
        raw_arguments: str,
        *,
        trace_id: str,
        request_id: str,
    ) -> tuple[ToolExecutionResult, dict[str, Any]]:
        try:
            parsed = json.loads(raw_arguments)
            if not isinstance(parsed, dict):
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            return (
                ToolExecutionResult(
                    status=ToolExecutionStatus.REJECTED,
                    error_code="INVALID_TOOL_ARGUMENTS",
                    output={
                        "ok": False,
                        "status": "rejected",
                        "error": {
                            "code": "INVALID_TOOL_ARGUMENTS",
                            "message": "Tool arguments must be a JSON object.",
                        },
                    },
                ),
                {},
            )
        result = await self._tool_router.execute(
            name,
            parsed,
            trace_id=trace_id,
            request_id=request_id,
        )
        return result, parsed


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _add_usage(total: dict[str, int], current: dict[str, int]) -> None:
    for key in ("inputTokens", "outputTokens", "totalTokens"):
        total[key] = total.get(key, 0) + current.get(key, 0)
