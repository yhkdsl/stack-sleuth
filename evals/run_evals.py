#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_SERVICE_ROOT = REPO_ROOT / "python-agent-service"
DEFAULT_SCENARIOS = REPO_ROOT / "evals" / "scenarios.yml"
DEFAULT_TRACE_DIR = REPO_ROOT / "var" / "eval-traces"


def _maybe_reexec_with_agent_venv() -> None:
    if os.environ.get("STACKSLEUTH_EVALS_BOOTSTRAPPED") == "1":
        return
    venv_python = AGENT_SERVICE_ROOT / ".venv" / "bin" / "python"
    if not venv_python.exists() or Path(sys.executable).resolve() == venv_python.resolve():
        return
    env = {**os.environ, "STACKSLEUTH_EVALS_BOOTSTRAPPED": "1"}
    raise SystemExit(
        subprocess.call([str(venv_python), *sys.argv], cwd=REPO_ROOT, env=env)
    )


if __name__ == "__main__":
    _maybe_reexec_with_agent_venv()

sys.path.insert(0, str(AGENT_SERVICE_ROOT))

from app.agent_loop import AgentLoop  # noqa: E402
from app.models import (  # noqa: E402
    AgentTrace,
    FunctionCall,
    ModelTurn,
    ToolExecutionResult,
    ToolExecutionStatus,
)
from app.trace_store import FileTraceStore  # noqa: E402


class EvalResult:
    def __init__(
        self,
        *,
        scenario_id: str,
        passed: bool,
        trace: AgentTrace,
        failures: list[str],
    ) -> None:
        self.scenario_id = scenario_id
        self.passed = passed
        self.trace = trace
        self.failures = failures


class ScriptedModelClient:
    def __init__(self, turns: list[dict[str, Any]]) -> None:
        self._turns = list(turns)

    async def create(
        self,
        *,
        input_items: str | list[dict[str, Any]],
    ) -> ModelTurn:
        if not self._turns:
            raise RuntimeError("scenario model turns exhausted")
        turn = self._turns.pop(0)
        calls = [
            FunctionCall(
                call_id=call["callId"],
                name=call["name"],
                arguments=json.dumps(
                    call.get("arguments", {}),
                    ensure_ascii=True,
                    separators=(",", ":"),
                ),
            )
            for call in turn.get("toolCalls", [])
        ]
        return ModelTurn(
            response_id=turn["responseId"],
            response_status=turn.get("responseStatus", "completed"),
            incomplete_reason=turn.get("incompleteReason"),
            response_error_code=turn.get("responseErrorCode"),
            output_text=turn.get("outputText", ""),
            function_calls=calls,
            continuation_items=[
                {
                    "type": "function_call",
                    "call_id": call.call_id,
                    "name": call.name,
                    "arguments": call.arguments,
                }
                for call in calls
            ],
            usage=turn.get(
                "usage",
                {"inputTokens": 8, "outputTokens": 2, "totalTokens": 10},
            ),
        )


class ScriptedToolRouter:
    def __init__(self, results: list[dict[str, Any]]) -> None:
        self._results = list(results)

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        trace_id: str,
        request_id: str,
    ) -> ToolExecutionResult:
        if not self._results:
            raise RuntimeError("scenario tool results exhausted")
        result = self._results.pop(0)
        return ToolExecutionResult(
            status=ToolExecutionStatus(result["status"]),
            output=result.get("output", {}),
            error_code=result.get("errorCode"),
            latency_ms=result.get("latencyMs", 0),
        )


def load_scenarios(path: Path = DEFAULT_SCENARIOS) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError("scenario file must contain a scenarios list")
    return scenarios


async def run_scenario(
    scenario: dict[str, Any],
    *,
    trace_dir: Path = DEFAULT_TRACE_DIR,
) -> EvalResult:
    scenario_id = scenario["id"]
    loop = AgentLoop(
        model_client=ScriptedModelClient(scenario["modelTurns"]),
        tool_router=ScriptedToolRouter(scenario.get("toolResults", [])),
        trace_store=FileTraceStore(trace_dir),
        model="eval-scripted-model",
        max_iterations=scenario["maxIterations"],
        request_timeout_seconds=scenario["requestTimeoutSeconds"],
    )
    trace = await loop.run(
        scenario["userRequest"],
        trace_id=f"eval_{scenario_id}",
    )
    failures = evaluate_trace(trace, scenario.get("expect", {}))
    return EvalResult(
        scenario_id=scenario_id,
        passed=not failures,
        trace=trace,
        failures=failures,
    )


def evaluate_trace(trace: AgentTrace, expect: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_status = expect.get("status")
    if expected_status is not None and trace.status.value != expected_status:
        failures.append(f"expected status {expected_status}, got {trace.status.value}")

    expected_trace_id = expect.get("traceId")
    if expected_trace_id is not None and trace.traceId != expected_trace_id:
        failures.append(f"expected traceId {expected_trace_id}, got {trace.traceId}")

    expected_error = expect.get("errorCode")
    if expected_error is not None:
        actual_error = trace.error["code"] if trace.error else None
        if actual_error != expected_error:
            failures.append(f"expected error {expected_error}, got {actual_error}")

    expected_calls = expect.get("toolCalls")
    if expected_calls is not None:
        actual_calls = [call.name for call in trace.toolCalls]
        if actual_calls != expected_calls:
            failures.append(f"expected tool calls {expected_calls}, got {actual_calls}")

    _expect_codes(
        failures,
        label="guardrail codes",
        expected=expect.get("guardrailCodes"),
        actual=[item.errorCode for item in trace.guardrailRejections],
    )
    _expect_codes(
        failures,
        label="tool error codes",
        expected=expect.get("toolErrorCodes"),
        actual=[item.errorCode for item in trace.toolResults if item.errorCode],
    )

    final_answer = trace.finalAnswer or ""
    for expected_text in expect.get("finalAnswerContains", []):
        if expected_text not in final_answer:
            failures.append(f"final answer did not contain {expected_text!r}")

    for evidence in expect.get("evidence", []):
        actual_value = _find_evidence(trace, evidence["tool"], evidence["path"])
        if actual_value != evidence.get("equals"):
            failures.append(
                "expected evidence "
                f"{evidence['tool']}.{evidence['path']}={evidence.get('equals')!r}, "
                f"got {actual_value!r}"
            )
    return failures


def _expect_codes(
    failures: list[str],
    *,
    label: str,
    expected: list[str] | None,
    actual: list[str | None],
) -> None:
    if expected is None:
        return
    if actual != expected:
        failures.append(f"expected {label} {expected}, got {actual}")


def _find_evidence(trace: AgentTrace, tool_name: str, path: str) -> Any:
    for result in trace.toolResults:
        if result.name == tool_name:
            return _get_path(result.output, path)
    return None


def _get_path(payload: Any, path: str) -> Any:
    value = payload
    for part in path.split("."):
        if isinstance(value, list):
            value = value[int(part)]
        elif isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


async def run_all(scenarios_path: Path, trace_dir: Path) -> list[EvalResult]:
    scenarios = load_scenarios(scenarios_path)
    trace_dir.mkdir(parents=True, exist_ok=True)
    results: list[EvalResult] = []
    for scenario in scenarios:
        results.append(await run_scenario(scenario, trace_dir=trace_dir))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run StackSleuth deterministic agent eval scenarios.",
    )
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--trace-dir", type=Path, default=DEFAULT_TRACE_DIR)
    args = parser.parse_args(argv)

    results = asyncio.run(run_all(args.scenarios, args.trace_dir))
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.scenario_id} trace={result.trace.traceId}")
        for failure in result.failures:
            print(f"  - {failure}")
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
