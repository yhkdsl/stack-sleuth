import argparse
import os
from collections.abc import Mapping, Sequence
from typing import TextIO

import httpx

from ops_agent.client import AgentApiClient
from ops_agent.formatting import print_error, print_request_failure, print_trace

DEFAULT_AGENT_URL = "http://localhost:8000"
DEFAULT_DASHBOARD_URL = "http://localhost:3000"
DEFAULT_TIMEOUT_SECONDS = 10.0


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    import sys

    resolved_stdout = stdout or sys.stdout
    resolved_stderr = stderr or sys.stderr
    resolved_env = env or os.environ
    parser = _build_parser(resolved_env)
    args = parser.parse_args(list(argv) if argv is not None else None)
    client = AgentApiClient(
        args.agent_url,
        timeout_seconds=args.timeout_seconds,
    )
    try:
        if args.command == "ask":
            return _handle_ask(args, client, stdout=resolved_stdout, stderr=resolved_stderr)
        if args.command == "trace":
            return _handle_trace(args, client, stdout=resolved_stdout, stderr=resolved_stderr)
    except (httpx.HTTPError, OSError, TimeoutError):
        print_request_failure(stderr=resolved_stderr)
        return 1
    return 1


def _build_parser(env: Mapping[str, str] | None = None) -> argparse.ArgumentParser:
    resolved_env = env or os.environ
    parser = argparse.ArgumentParser(
        prog="ops-agent",
        description="Run and replay StackSleuth backend investigations.",
    )
    parser.set_defaults(
        agent_url=resolved_env.get("STACKSLEUTH_AGENT_URL", DEFAULT_AGENT_URL),
        dashboard_url=resolved_env.get("STACKSLEUTH_DASHBOARD_URL", DEFAULT_DASHBOARD_URL),
        timeout_seconds=_parse_timeout_seconds(
            resolved_env.get("STACKSLEUTH_AGENT_TIMEOUT_SECONDS")
        ),
    )
    parser.add_argument("--agent-url", default=argparse.SUPPRESS)
    parser.add_argument("--dashboard-url", default=argparse.SUPPRESS)
    parser.add_argument("--timeout-seconds", type=float, default=argparse.SUPPRESS)

    subparsers = parser.add_subparsers(dest="command", required=True)
    ask = subparsers.add_parser("ask", help="Run a new investigation.")
    ask.add_argument("request")
    ask.add_argument("--verbose", action="store_true")
    ask.add_argument("--open-trace", action="store_true")

    trace = subparsers.add_parser("trace", help="Inspect saved traces.")
    trace_subparsers = trace.add_subparsers(dest="trace_command", required=True)
    show = trace_subparsers.add_parser("show", help="Show a saved trace summary.")
    show.add_argument("trace_id")
    show.add_argument("--verbose", action="store_true")
    replay = trace_subparsers.add_parser("replay", help="Replay a saved trace.")
    replay.add_argument("trace_id")
    replay.add_argument("--verbose", action="store_true")
    return parser


def _handle_ask(
    args: argparse.Namespace,
    client: AgentApiClient,
    *,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    result = client.run(args.request)
    if not _looks_like_trace(result.payload):
        print_error(result.payload, stderr=stderr)
        return 1
    print_trace(
        result.payload,
        stdout=stdout,
        verbose=args.verbose,
        dashboard_url=args.dashboard_url if args.open_trace else None,
    )
    return 0 if result.status_code < 400 and result.payload.get("status") == "completed" else 1


def _handle_trace(
    args: argparse.Namespace,
    client: AgentApiClient,
    *,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    result = client.get_trace(args.trace_id)
    if not _looks_like_trace(result.payload):
        print_error(result.payload, stderr=stderr)
        return 1
    print_trace(
        result.payload,
        stdout=stdout,
        verbose=args.verbose,
        replay=args.trace_command == "replay",
    )
    return 0 if result.status_code < 400 else 1


def _looks_like_trace(payload: dict[str, object]) -> bool:
    return "traceId" in payload and "status" in payload


def _parse_timeout_seconds(raw_value: str | None) -> float:
    if raw_value is None:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        timeout_seconds = float(raw_value)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    return timeout_seconds if timeout_seconds > 0 else DEFAULT_TIMEOUT_SECONDS
