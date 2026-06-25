"""Run the real StackSleuth agent loop without OpenAI or Spring credentials."""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

SERVICE_ROOT = Path(__file__).resolve().parents[2] / "python-agent-service"
sys.path.insert(0, str(SERVICE_ROOT))

from app.agent_loop import AgentLoop  # noqa: E402
from app.models import (  # noqa: E402
    FunctionCall,
    ModelTurn,
    ToolExecutionResult,
    ToolExecutionStatus,
)
from app.trace_store import FileTraceStore  # noqa: E402


class ScriptedModel:
    def __init__(self) -> None:
        self.turn = 0

    async def create(
        self,
        *,
        input_items: str | list[dict[str, Any]],
    ) -> ModelTurn:
        self.turn += 1
        if self.turn == 1:
            arguments = json.dumps(
                {"keyword": "ERROR", "sinceMinutes": 60, "limit": 20}
            )
            return ModelTurn(
                response_id="mock-response-1",
                output_text="",
                function_calls=[
                    FunctionCall(
                        call_id="mock-call-logs",
                        name="search_error_logs",
                        arguments=arguments,
                    )
                ],
                continuation_items=[
                    {
                        "type": "function_call",
                        "call_id": "mock-call-logs",
                        "name": "search_error_logs",
                        "arguments": arguments,
                    }
                ],
                usage={"inputTokens": 15, "outputTokens": 5, "totalTokens": 20},
            )
        return ModelTurn(
            response_id="mock-response-2",
            output_text=(
                "Three recent errors reference synthetic user 42. "
                "A database check is required to confirm the cause."
            ),
            function_calls=[],
            continuation_items=[],
            usage={"inputTokens": 25, "outputTokens": 12, "totalTokens": 37},
        )


class ScriptedToolRouter:
    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        trace_id: str,
        request_id: str,
    ) -> ToolExecutionResult:
        assert name == "search_error_logs"
        return ToolExecutionResult(
            status=ToolExecutionStatus.SUCCESS,
            output={
                "matchCount": 3,
                "matches": [
                    {
                        "requestId": "req-demo-4201",
                        "message": "ERROR NullPointerException user_id=42",
                    }
                ],
            },
            latency_ms=1,
        )


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="stack-sleuth-demo-") as directory:
        loop = AgentLoop(
            model_client=ScriptedModel(),
            tool_router=ScriptedToolRouter(),
            trace_store=FileTraceStore(Path(directory)),
            model="mock-model",
            max_iterations=5,
            request_timeout_seconds=2,
        )
        trace = await loop.run(
            "Investigate errors from the last hour",
            trace_id="trace_mock_demo",
        )
        print(trace.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
