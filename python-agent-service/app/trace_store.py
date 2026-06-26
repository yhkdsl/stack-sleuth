import asyncio
import re
import tempfile
import time
from pathlib import Path

from app.models import AgentTrace, RedactionEvent
from app.redaction import redact

_SAFE_TRACE_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class TraceNotFoundError(Exception):
    pass


class FileTraceStore:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def sanitize(self, trace: AgentTrace) -> AgentTrace:
        payload, events = redact(trace.model_dump(mode="json"))
        existing_events = [RedactionEvent.model_validate(item) for item in payload["redactions"]]
        payload["redactions"] = [
            event.model_dump(mode="json") for event in [*existing_events, *events]
        ]
        return AgentTrace.model_validate(payload)

    async def save(
        self,
        trace: AgentTrace,
        *,
        request_started: float | None = None,
    ) -> AgentTrace:
        if not _SAFE_TRACE_ID.fullmatch(trace.traceId):
            raise ValueError("invalid trace ID")
        sanitized = self.sanitize(trace)
        sanitized.persisted = True
        sanitized.persistenceError = None
        write_task = asyncio.create_task(
            asyncio.to_thread(self._write_temporary, sanitized, request_started)
        )
        try:
            temporary_path = await asyncio.shield(write_task)
        except asyncio.CancelledError:
            write_task.add_done_callback(self._discard_temporary)
            raise
        destination = self._directory / f"{sanitized.traceId}.json"
        temporary_path.replace(destination)
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

    def _write_temporary(
        self,
        trace: AgentTrace,
        request_started: float | None = None,
    ) -> Path:
        self._directory.mkdir(parents=True, exist_ok=True)
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
            temporary.flush()
            if request_started is not None:
                trace.totalDurationMs = round(
                    (time.perf_counter() - request_started) * 1000
                )
                temporary.seek(0)
                temporary.truncate()
                temporary.write(trace.model_dump_json(indent=2))
                temporary.write("\n")
            temporary_path = Path(temporary.name)
        return temporary_path

    @staticmethod
    def _discard_temporary(task: asyncio.Task[Path]) -> None:
        try:
            temporary_path = task.result()
        except BaseException:
            return
        temporary_path.unlink(missing_ok=True)
