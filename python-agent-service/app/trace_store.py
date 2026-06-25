import asyncio
import re
import tempfile
from pathlib import Path

from app.models import AgentTrace, RedactionEvent
from app.redaction import redact

_SAFE_TRACE_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class TraceNotFoundError(Exception):
    pass


class FileTraceStore:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    async def save(self, trace: AgentTrace) -> AgentTrace:
        if not _SAFE_TRACE_ID.fullmatch(trace.traceId):
            raise ValueError("invalid trace ID")
        payload, events = redact(trace.model_dump(mode="json"))
        existing_events = [RedactionEvent.model_validate(item) for item in payload["redactions"]]
        payload["redactions"] = [
            event.model_dump(mode="json") for event in [*existing_events, *events]
        ]
        sanitized = AgentTrace.model_validate(payload)
        await asyncio.to_thread(self._write, sanitized)
        return sanitized

    async def get(self, trace_id: str) -> AgentTrace:
        if not _SAFE_TRACE_ID.fullmatch(trace_id):
            raise TraceNotFoundError(trace_id)
        path = self._directory / f"{trace_id}.json"
        try:
            raw = await asyncio.to_thread(path.read_text, encoding="utf-8")
        except FileNotFoundError as exception:
            raise TraceNotFoundError(trace_id) from exception
        return AgentTrace.model_validate_json(raw)

    def _write(self, trace: AgentTrace) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)
        destination = self._directory / f"{trace.traceId}.json"
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self._directory,
            prefix=f".{trace.traceId}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(trace.model_dump_json(indent=2))
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        temporary_path.replace(destination)
