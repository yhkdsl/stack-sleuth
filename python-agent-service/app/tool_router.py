import json
import time
from typing import Any

import httpx

from app.models import ToolExecutionResult, ToolExecutionStatus

_TOOL_PATHS = {
    "check_server_health": "/internal/tools/health",
    "search_error_logs": "/internal/tools/logs/search",
    "run_read_only_query": "/internal/tools/sql/read-only",
}


class SpringToolRouter:
    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        timeout_seconds: float,
        max_output_chars: int,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout_seconds = timeout_seconds
        self._max_output_chars = max_output_chars
        self._client = client

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        trace_id: str,
        request_id: str,
    ) -> ToolExecutionResult:
        path = _TOOL_PATHS.get(name)
        if path is None:
            return self._error(
                ToolExecutionStatus.REJECTED,
                "TOOL_NOT_ALLOWED",
                f"Tool '{name}' is not registered.",
            )

        started = time.perf_counter()
        try:
            response = await self._post(path, arguments, trace_id, request_id)
        except httpx.TimeoutException:
            result = self._error(
                ToolExecutionStatus.TIMED_OUT,
                "TOOL_TIMEOUT",
                f"Tool call exceeded {self._timeout_seconds:g} seconds.",
            )
        except httpx.RequestError:
            result = self._error(
                ToolExecutionStatus.FAILED,
                "TOOL_UNAVAILABLE",
                "Spring tool server is unavailable.",
            )
        else:
            result = self._from_response(response)

        result.latency_ms = round((time.perf_counter() - started) * 1000)
        return result

    async def _post(
        self,
        path: str,
        arguments: dict[str, Any],
        trace_id: str,
        request_id: str,
    ) -> httpx.Response:
        headers = {
            "X-Tool-Server-Token": self._token,
            "X-Trace-Id": trace_id,
            "X-Request-Id": request_id,
        }
        if self._client is not None:
            return await self._client.post(
                f"{self._base_url}{path}",
                json=arguments,
                headers=headers,
                timeout=self._timeout_seconds,
            )
        async with httpx.AsyncClient() as client:
            return await client.post(
                f"{self._base_url}{path}",
                json=arguments,
                headers=headers,
                timeout=self._timeout_seconds,
            )

    def _from_response(self, response: httpx.Response) -> ToolExecutionResult:
        try:
            body = response.json()
        except ValueError:
            return self._error(
                ToolExecutionStatus.FAILED,
                "TOOL_INVALID_RESPONSE",
                "Tool server returned invalid JSON.",
            )
        if not isinstance(body, dict):
            return self._error(
                ToolExecutionStatus.FAILED,
                "TOOL_INVALID_RESPONSE",
                "Tool server returned a non-object JSON response.",
            )

        if response.is_success:
            return ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                output=self._bounded_output(body),
            )

        status = (
            ToolExecutionStatus.REJECTED
            if 400 <= response.status_code < 500
            else ToolExecutionStatus.FAILED
        )
        code = body.get("code", f"TOOL_HTTP_{response.status_code}")
        message = body.get("message", "Tool server returned an error.")
        return self._error(status, code, message)

    def _bounded_output(self, body: Any) -> dict[str, Any]:
        serialized = json.dumps(body, separators=(",", ":"), ensure_ascii=True)
        if len(serialized) <= self._max_output_chars and isinstance(body, dict):
            return body
        return {
            "truncated": True,
            "content": serialized[: self._max_output_chars],
            "originalChars": len(serialized),
        }

    @staticmethod
    def _error(
        status: ToolExecutionStatus,
        code: str,
        message: str,
    ) -> ToolExecutionResult:
        return ToolExecutionResult(
            status=status,
            error_code=code,
            output={
                "ok": False,
                "status": status.value,
                "error": {"code": code, "message": message},
            },
        )
