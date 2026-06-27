import json
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class ApiResult:
    status_code: int
    payload: dict[str, Any]


class AgentApiClient:
    def __init__(self, base_url: str, *, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def run(self, request: str) -> ApiResult:
        return self._request(
            "POST",
            "/agent/run",
            payload={"request": request},
        )

    def get_trace(self, trace_id: str) -> ApiResult:
        return self._request("GET", f"/agent/traces/{trace_id}")

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> ApiResult:
        headers = {"Content-Type": "application/json"} if payload is not None else None
        content = (
            json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
            if payload is not None
            else None
        )
        with httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
        ) as client:
            response = client.request(method, path, headers=headers, content=content)
        try:
            response_payload = response.json()
        except ValueError:
            response_payload = {
                "code": "INVALID_AGENT_RESPONSE",
                "message": "Agent service returned a non-JSON response.",
            }
        if not isinstance(response_payload, dict):
            response_payload = {
                "code": "INVALID_AGENT_RESPONSE",
                "message": "Agent service returned an invalid JSON shape.",
            }
        return ApiResult(status_code=response.status_code, payload=response_payload)
