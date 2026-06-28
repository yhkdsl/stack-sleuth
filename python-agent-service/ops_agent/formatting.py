import json
from typing import Any, TextIO

from app.redaction import redact

MAX_VERBOSE_OUTPUT_CHARS = 2000


def print_trace(
    trace: dict[str, Any],
    *,
    stdout: TextIO,
    verbose: bool = False,
    replay: bool = False,
    dashboard_url: str | None = None,
) -> None:
    safe_trace = _safe(trace)
    if replay:
        print("Replay loaded from persisted trace", file=stdout)
        print("", file=stdout)

    final_answer = safe_trace.get("finalAnswer")
    if final_answer:
        print("Final answer", file=stdout)
        print(final_answer, file=stdout)
        print("", file=stdout)

    print(f"Trace: {safe_trace.get('traceId', 'unknown')}", file=stdout)
    print(f"Status: {safe_trace.get('status', 'unknown')}", file=stdout)
    duration = safe_trace.get("totalDurationMs")
    if isinstance(duration, int | float):
        print(f"Duration: {duration:g} ms", file=stdout)

    tool_results = safe_trace.get("toolResults")
    if isinstance(tool_results, list) and tool_results:
        print("", file=stdout)
        print("Evidence", file=stdout)
        for result in tool_results:
            if isinstance(result, dict):
                print(f"- {_tool_result_summary(result)}", file=stdout)

    if dashboard_url and safe_trace.get("traceId") and safe_trace.get("persisted") is True:
        print("", file=stdout)
        print(f"Dashboard: {dashboard_url.rstrip('/')}/traces/{safe_trace['traceId']}", file=stdout)
    elif dashboard_url and safe_trace.get("traceId"):
        persistence_error = safe_trace.get("persistenceError")
        if isinstance(persistence_error, dict):
            code = persistence_error.get("code", "TRACE_NOT_PERSISTED")
            print("", file=stdout)
            print(f"Trace replay unavailable: {code}", file=stdout)

    if verbose:
        _print_verbose(safe_trace, stdout=stdout)


def print_error(payload: dict[str, Any], *, stderr: TextIO) -> None:
    safe_payload = _safe(payload)
    nested_error = safe_payload.get("error")
    nested_error_dict = nested_error if isinstance(nested_error, dict) else {}
    code = safe_payload.get("code") or nested_error_dict.get("code")
    if not isinstance(code, str):
        code = "AGENT_REQUEST_FAILED"
    message = safe_payload.get("message") or nested_error_dict.get("message")
    if not isinstance(message, str) and isinstance(nested_error, str):
        message = nested_error
    if not isinstance(message, str):
        message = "Agent request failed."
    message = _sanitize_error_message(message)
    print(f"{code}: {message}", file=stderr)


def print_request_failure(*, stderr: TextIO) -> None:
    print("REQUEST_FAILED: Could not reach the StackSleuth agent service.", file=stderr)


def _print_verbose(trace: dict[str, Any], *, stdout: TextIO) -> None:
    print("", file=stdout)
    print("Tool calls", file=stdout)
    tool_calls = trace.get("toolCalls")
    if isinstance(tool_calls, list) and tool_calls:
        for index, call in enumerate(tool_calls, start=1):
            if isinstance(call, dict):
                print(
                    f"{index}. {call.get('name', 'unknown')} "
                    f"(iteration {call.get('iteration', 'unknown')})",
                    file=stdout,
                )
    else:
        print("- none", file=stdout)

    tool_results = trace.get("toolResults")
    if isinstance(tool_results, list) and tool_results:
        print("", file=stdout)
        print("Tool results", file=stdout)
        for index, result in enumerate(tool_results, start=1):
            if isinstance(result, dict):
                name = result.get("name", "unknown")
                status = result.get("status", "unknown")
                print(f"{index}. {name}: {status}", file=stdout)
                print(_format_json(result.get("output", {})), file=stdout)

    guardrails = trace.get("guardrailRejections")
    if isinstance(guardrails, list) and guardrails:
        print("", file=stdout)
        print("Guardrail rejections", file=stdout)
        for rejection in guardrails:
            if isinstance(rejection, dict):
                print(f"- {_tool_result_summary(rejection)}", file=stdout)

    redactions = trace.get("redactions")
    if isinstance(redactions, list) and redactions:
        print("", file=stdout)
        print("Redactions", file=stdout)
        for event in redactions:
            if isinstance(event, dict):
                print(
                    f"- {event.get('path', 'unknown')}: {event.get('reason', 'redacted')}",
                    file=stdout,
                )

    usage = trace.get("usage")
    if isinstance(usage, dict):
        total = usage.get("totalTokens")
        if isinstance(total, int):
            print("", file=stdout)
            print(f"Usage: {total} tokens", file=stdout)


def _tool_result_summary(result: dict[str, Any]) -> str:
    name = result.get("name", "unknown")
    status = result.get("status", "unknown")
    error_code = result.get("errorCode")
    latency = result.get("latencyMs")
    suffix = f" {error_code}" if error_code else ""
    if isinstance(latency, int | float):
        return f"{name}: {status}{suffix} ({latency:g} ms)"
    return f"{name}: {status}{suffix}"


def _safe(value: Any) -> Any:
    safe_value, _ = redact(value)
    return safe_value


def _format_json(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True)
    if len(rendered) <= MAX_VERBOSE_OUTPUT_CHARS:
        return rendered
    return f"{rendered[:MAX_VERBOSE_OUTPUT_CHARS]}...\n[truncated]"


def _sanitize_error_message(message: str) -> str:
    replacements = {
        "OPENAI_API_KEY": "agent credentials",
        "AGENT_MODEL": "agent model",
        "TOOL_SERVER_TOKEN": "tool-server credentials",
        "DB password": "database credentials",
        "database password": "database credentials",
        "access token": "access credentials",
    }
    cleaned = message
    for needle, replacement in replacements.items():
        cleaned = cleaned.replace(needle, replacement)
    safe, _ = redact(cleaned)
    return safe
