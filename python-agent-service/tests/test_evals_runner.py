import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = REPO_ROOT / "evals" / "run_evals.py"
SCENARIOS_PATH = REPO_ROOT / "evals" / "scenarios.yml"


def load_runner():
    spec = importlib.util.spec_from_file_location("stacksleuth_evals_runner", RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_eval_scenarios_cover_required_failure_modes() -> None:
    runner = load_runner()

    scenarios = runner.load_scenarios(SCENARIOS_PATH)

    assert {scenario["id"] for scenario in scenarios} == {
        "null_profile_image_incident",
        "destructive_sql_rejection",
        "tool_timeout",
        "max_iteration_stop",
    }


async def test_eval_runner_verifies_happy_path_tool_sequence(tmp_path: Path) -> None:
    runner = load_runner()
    scenario = next(
        item
        for item in runner.load_scenarios(SCENARIOS_PATH)
        if item["id"] == "null_profile_image_incident"
    )

    result = await runner.run_scenario(scenario, trace_dir=tmp_path)

    assert result.passed is True
    assert result.trace.traceId == "eval_null_profile_image_incident"
    assert result.trace.status == "completed"
    assert [call.name for call in result.trace.toolCalls] == [
        "search_error_logs",
        "run_read_only_query",
    ]


async def test_eval_runner_verifies_failure_contracts(tmp_path: Path) -> None:
    runner = load_runner()
    scenarios = {
        item["id"]: item for item in runner.load_scenarios(SCENARIOS_PATH)
    }

    destructive = await runner.run_scenario(
        scenarios["destructive_sql_rejection"],
        trace_dir=tmp_path,
    )
    timeout = await runner.run_scenario(scenarios["tool_timeout"], trace_dir=tmp_path)
    max_iterations = await runner.run_scenario(
        scenarios["max_iteration_stop"],
        trace_dir=tmp_path,
    )

    assert destructive.passed is True
    assert destructive.trace.guardrailRejections[0].errorCode == "SQL_WRITE_BLOCKED"
    assert timeout.passed is True
    assert timeout.trace.traceId == "eval_tool_timeout"
    assert timeout.trace.status == "incomplete"
    assert timeout.trace.toolResults[0].errorCode == "TOOL_TIMEOUT"
    assert max_iterations.passed is True
    assert max_iterations.trace.error["code"] == "MAX_ITERATIONS_REACHED"


def test_eval_runner_main_returns_success(tmp_path: Path) -> None:
    runner = load_runner()

    exit_code = runner.main(
        [
            "--scenarios",
            str(SCENARIOS_PATH),
            "--trace-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
