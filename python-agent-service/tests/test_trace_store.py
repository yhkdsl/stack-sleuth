import json
from pathlib import Path

import pytest

from app.models import AgentTrace, TraceStatus
from app.trace_store import FileTraceStore, TraceNotFoundError


def build_trace() -> AgentTrace:
    return AgentTrace(
        traceId="trace_test_123",
        status=TraceStatus.COMPLETED,
        startedAt="2026-06-25T00:00:00Z",
        completedAt="2026-06-25T00:00:01Z",
        userRequest="Investigate developer@example.com",
        model="test-model",
        iterations=1,
        toolCalls=[],
        toolResults=[],
        guardrailRejections=[],
        redactions=[],
        usage={"totalTokens": 12},
        estimatedCost=None,
        pricingMetadata=None,
        totalDurationMs=1000,
        confidence=None,
        finalAnswer="Bearer secret-token",
    )


async def test_trace_store_persists_only_redacted_json(tmp_path: Path) -> None:
    store = FileTraceStore(tmp_path)

    stored = await store.save(build_trace())

    raw = (tmp_path / "trace_test_123.json").read_text()
    assert "developer@example.com" not in raw
    assert "secret-token" not in raw
    assert stored.userRequest == "Investigate [REDACTED]"
    assert stored.finalAnswer == "[REDACTED]"
    assert len(stored.redactions) >= 2
    assert json.loads(raw)["traceId"] == "trace_test_123"


async def test_trace_store_loads_trace_without_external_calls(tmp_path: Path) -> None:
    store = FileTraceStore(tmp_path)
    await store.save(build_trace())

    loaded = await store.get("trace_test_123")

    assert loaded.traceId == "trace_test_123"
    assert loaded.status is TraceStatus.COMPLETED


async def test_trace_store_rejects_missing_or_unsafe_trace_ids(tmp_path: Path) -> None:
    store = FileTraceStore(tmp_path)

    with pytest.raises(TraceNotFoundError):
        await store.get("../../.env")

    with pytest.raises(TraceNotFoundError):
        await store.get("trace_missing")


async def test_trace_store_rejects_unsafe_trace_id_before_persistence(
    tmp_path: Path,
) -> None:
    store = FileTraceStore(tmp_path)
    trace = build_trace()
    trace.traceId = "../../outside"

    with pytest.raises(ValueError, match="invalid trace ID"):
        await store.save(trace)
