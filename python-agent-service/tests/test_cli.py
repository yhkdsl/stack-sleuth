from io import StringIO
from typing import Any

import respx
from httpx import Response

from ops_agent.main import main


def trace_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "traceId": "trace_cli_123",
        "status": "completed",
        "startedAt": "2026-06-27T00:00:00Z",
        "completedAt": "2026-06-27T00:00:01Z",
        "userRequest": "Investigate recent errors",
        "model": "test-model",
        "iterations": 2,
        "toolCalls": [
            {
                "callId": "call-logs",
                "requestId": "req-logs",
                "name": "search_error_logs",
                "arguments": {"keyword": "ERROR", "sinceMinutes": 60, "limit": 20},
                "iteration": 1,
            }
        ],
        "toolResults": [
            {
                "callId": "call-logs",
                "requestId": "req-logs",
                "name": "search_error_logs",
                "status": "success",
                "output": {"matchCount": 3},
                "errorCode": None,
                "latencyMs": 12,
            }
        ],
        "guardrailRejections": [],
        "redactions": [],
        "usage": {"inputTokens": 12, "outputTokens": 5, "totalTokens": 17},
        "estimatedCost": None,
        "pricingMetadata": None,
        "totalDurationMs": 1000,
        "persisted": True,
        "persistenceError": None,
        "confidence": None,
        "finalAnswer": "Three errors were found in the last hour.",
        "error": None,
    }
    payload.update(overrides)
    return payload


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    exit_code = main(
        list(args),
        stdout=stdout,
        stderr=stderr,
        env={
            "STACKSLEUTH_AGENT_URL": "http://agent.test",
            "STACKSLEUTH_DASHBOARD_URL": "http://dashboard.test",
        },
    )
    return exit_code, stdout.getvalue(), stderr.getvalue()


def run_cli_with_env(*args: str, env: dict[str, str]) -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    exit_code = main(
        list(args),
        stdout=stdout,
        stderr=stderr,
        env=env,
    )
    return exit_code, stdout.getvalue(), stderr.getvalue()


@respx.mock
def test_ask_prints_final_answer_trace_id_and_compact_evidence() -> None:
    route = respx.post("http://agent.test/agent/run").mock(
        return_value=Response(200, json=trace_payload())
    )

    exit_code, stdout, stderr = run_cli("ask", "Investigate recent errors")

    assert exit_code == 0
    assert stderr == ""
    assert stdout.index("Final answer") < stdout.index("Trace")
    assert "Three errors were found in the last hour." in stdout
    assert "Trace: trace_cli_123" in stdout
    assert "search_error_logs: success (12 ms)" in stdout
    assert route.calls.last.request.url.path == "/agent/run"
    assert route.calls.last.request.content == b'{"request":"Investigate recent errors"}'


@respx.mock
def test_ask_verbose_prints_ordered_tool_calls_redactions_and_usage() -> None:
    payload = trace_payload(
        toolResults=[
            {
                "callId": "call-logs",
                "requestId": "req-logs",
                "name": "search_error_logs",
                "status": "success",
                "output": {
                    "matchCount": 3,
                    "matches": [{"message": "Synthetic NullPointerException"}],
                },
                "errorCode": None,
                "latencyMs": 12,
            }
        ],
        guardrailRejections=[
            {
                "callId": "call-sql",
                "requestId": "req-sql",
                "name": "run_read_only_query",
                "status": "rejected",
                "output": {"error": {"code": "SQL_WRITE_BLOCKED"}},
                "errorCode": "SQL_WRITE_BLOCKED",
                "latencyMs": 3,
            }
        ],
        redactions=[{"path": "$.toolResults[0].output.email", "reason": "email"}],
    )
    respx.post("http://agent.test/agent/run").mock(return_value=Response(409, json=payload))

    exit_code, stdout, stderr = run_cli("ask", "Delete users", "--verbose")

    assert exit_code == 1
    assert stderr == ""
    assert "Tool calls" in stdout
    assert "1. search_error_logs" in stdout
    assert "Tool results" in stdout
    assert "Synthetic NullPointerException" in stdout
    assert "Guardrail rejections" in stdout
    assert "SQL_WRITE_BLOCKED" in stdout
    assert "Redactions" in stdout
    assert "$.toolResults[0].output.email" in stdout
    assert "Usage: 17 tokens" in stdout


@respx.mock
def test_ask_open_trace_prints_dashboard_url_without_browser_side_effect() -> None:
    respx.post("http://agent.test/agent/run").mock(
        return_value=Response(200, json=trace_payload())
    )

    exit_code, stdout, _ = run_cli("ask", "Investigate recent errors", "--open-trace")

    assert exit_code == 0
    assert "Dashboard: http://dashboard.test/traces/trace_cli_123" in stdout


@respx.mock
def test_ask_open_trace_does_not_print_dashboard_url_when_trace_was_not_persisted() -> None:
    respx.post("http://agent.test/agent/run").mock(
        return_value=Response(
            504,
            json=trace_payload(
                status="failed",
                persisted=False,
                persistenceError={
                    "code": "TRACE_PERSISTENCE_TIMEOUT",
                    "message": "Trace persistence budget expired.",
                },
                error={"code": "REQUEST_TIMEOUT", "message": "Agent execution timed out."},
            ),
        )
    )

    exit_code, stdout, _ = run_cli("ask", "Investigate recent errors", "--open-trace")

    assert exit_code == 1
    assert "Dashboard:" not in stdout
    assert "Trace replay unavailable: TRACE_PERSISTENCE_TIMEOUT" in stdout


@respx.mock
def test_trace_show_replays_existing_trace_without_agent_run() -> None:
    show_route = respx.get("http://agent.test/agent/traces/trace_cli_123").mock(
        return_value=Response(200, json=trace_payload())
    )

    exit_code, stdout, stderr = run_cli("trace", "show", "trace_cli_123")

    assert exit_code == 0
    assert stderr == ""
    assert "Final answer" in stdout
    assert "Trace: trace_cli_123" in stdout
    assert show_route.called
    assert [call.request.url.path for call in respx.calls] == [
        "/agent/traces/trace_cli_123"
    ]


@respx.mock
def test_trace_replay_labels_replay_and_fetches_trace_only() -> None:
    respx.get("http://agent.test/agent/traces/trace_cli_123").mock(
        return_value=Response(200, json=trace_payload())
    )

    exit_code, stdout, _ = run_cli("trace", "replay", "trace_cli_123")

    assert exit_code == 0
    assert "Replay loaded from persisted trace" in stdout
    assert "Final answer" in stdout
    assert [call.request.url.path for call in respx.calls] == [
        "/agent/traces/trace_cli_123"
    ]


@respx.mock
def test_api_error_prints_structured_error_without_secret_leak() -> None:
    respx.post("http://agent.test/agent/run").mock(
        return_value=Response(
            503,
            json={
                "code": "AGENT_NOT_CONFIGURED",
                "message": "Set OPENAI_API_KEY and AGENT_MODEL to enable live agent runs.",
            },
        )
    )

    exit_code, stdout, stderr = run_cli("ask", "Investigate")

    assert exit_code == 1
    assert stdout == ""
    assert "AGENT_NOT_CONFIGURED" in stderr
    assert "OPENAI_API_KEY" not in stderr
    assert "AGENT_MODEL" not in stderr


@respx.mock
def test_api_error_with_string_error_shape_prints_safe_fallback() -> None:
    respx.post("http://agent.test/agent/run").mock(
        return_value=Response(502, json={"error": "upstream failed"})
    )

    exit_code, stdout, stderr = run_cli("ask", "Investigate")

    assert exit_code == 1
    assert stdout == ""
    assert "AGENT_REQUEST_FAILED" in stderr
    assert "upstream failed" in stderr


@respx.mock
def test_cli_output_redacts_sensitive_values_from_trace() -> None:
    respx.post("http://agent.test/agent/run").mock(
        return_value=Response(
            200,
            json=trace_payload(
                finalAnswer="Contact developer@example.test with Bearer secret-token",
                toolResults=[
                    {
                        "callId": "call-logs",
                        "requestId": "req-logs",
                        "name": "search_error_logs",
                        "status": "success",
                        "output": {
                            "email": "developer@example.test",
                            "phone": "+1-415-555-0100",
                        },
                        "errorCode": None,
                        "latencyMs": 12,
                    }
                ],
            ),
        )
    )

    exit_code, stdout, stderr = run_cli("ask", "Investigate recent errors")

    assert exit_code == 0
    assert stderr == ""
    assert "[REDACTED]" in stdout
    assert "developer@example.test" not in stdout
    assert "secret-token" not in stdout
    assert "415-555-0100" not in stdout


@respx.mock
def test_connection_error_prints_safe_message() -> None:
    respx.post("http://agent.test/agent/run").mock(side_effect=TimeoutError)

    exit_code, stdout, stderr = run_cli("ask", "Investigate")

    assert exit_code == 1
    assert stdout == ""
    assert "REQUEST_FAILED" in stderr
    assert "agent.test" not in stderr


@respx.mock
def test_invalid_timeout_env_falls_back_without_traceback() -> None:
    respx.post("http://agent.test/agent/run").mock(
        return_value=Response(200, json=trace_payload())
    )

    exit_code, stdout, stderr = run_cli_with_env(
        "ask",
        "Investigate",
        env={
            "STACKSLEUTH_AGENT_URL": "http://agent.test",
            "STACKSLEUTH_AGENT_TIMEOUT_SECONDS": "not-a-number",
        },
    )

    assert exit_code == 0
    assert "Trace: trace_cli_123" in stdout
    assert stderr == ""
