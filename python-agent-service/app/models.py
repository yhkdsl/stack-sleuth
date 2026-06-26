from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolExecutionStatus(StrEnum):
    SUCCESS = "success"
    REJECTED = "rejected"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class TraceStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


class RedactionEvent(BaseModel):
    path: str
    reason: str


class ToolExecutionResult(BaseModel):
    status: ToolExecutionStatus
    output: dict[str, Any]
    error_code: str | None = None
    latency_ms: int = 0


class ToolCallRecord(BaseModel):
    callId: str
    requestId: str
    name: str
    arguments: dict[str, Any]
    iteration: int


class ToolResultRecord(BaseModel):
    callId: str
    requestId: str
    name: str
    status: ToolExecutionStatus
    output: dict[str, Any]
    errorCode: str | None = None
    latencyMs: int


class AgentTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traceId: str
    status: TraceStatus
    startedAt: str
    completedAt: str | None
    userRequest: str
    model: str
    iterations: int
    toolCalls: list[ToolCallRecord]
    toolResults: list[ToolResultRecord]
    guardrailRejections: list[ToolResultRecord]
    redactions: list[RedactionEvent]
    usage: dict[str, int]
    estimatedCost: float | None
    pricingMetadata: dict[str, Any] | None
    totalDurationMs: int | None
    persisted: bool = False
    persistenceError: dict[str, str] | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    finalAnswer: str | None
    error: dict[str, str] | None = None


class FunctionCall(BaseModel):
    call_id: str
    name: str
    arguments: str


class ModelTurn(BaseModel):
    response_id: str
    response_status: str
    incomplete_reason: str | None = None
    response_error_code: str | None = None
    output_text: str
    function_calls: list[FunctionCall]
    continuation_items: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, int]
