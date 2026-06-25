from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from app.agent_loop import AgentLoop
from app.config import Settings
from app.models import AgentTrace, TraceStatus
from app.openai_client import OpenAIResponsesClient
from app.tool_router import SpringToolRouter
from app.trace_store import FileTraceStore, TraceNotFoundError


class AgentRunRequest(BaseModel):
    request: str

    @field_validator("request")
    @classmethod
    def request_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("request must not be blank")
        return stripped


def create_app(
    settings: Settings | None = None,
    *,
    agent_loop: Any | None = None,
    trace_store: FileTraceStore | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings()
    resolved_store = trace_store or FileTraceStore(resolved_settings.trace_directory)
    resolved_loop = agent_loop or _build_live_loop(resolved_settings, resolved_store)

    app = FastAPI(title="StackSleuth Agent Service", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.post("/agent/run", response_model=AgentTrace)
    async def run_agent(request: AgentRunRequest) -> AgentTrace | JSONResponse:
        if resolved_loop is None:
            return JSONResponse(
                status_code=503,
                content={
                    "code": "AGENT_NOT_CONFIGURED",
                    "message": (
                        "Set OPENAI_API_KEY and AGENT_MODEL to enable live agent runs."
                    ),
                },
            )

        trace = await resolved_loop.run(request.request)
        status_code = _status_code(trace)
        if status_code == 200:
            return trace
        return JSONResponse(
            status_code=status_code,
            content=trace.model_dump(mode="json"),
        )

    @app.get("/agent/traces/{trace_id}", response_model=AgentTrace)
    async def get_trace(trace_id: str) -> AgentTrace | JSONResponse:
        try:
            return await resolved_store.get(trace_id)
        except TraceNotFoundError:
            return JSONResponse(
                status_code=404,
                content={
                    "code": "TRACE_NOT_FOUND",
                    "message": "Trace was not found.",
                },
            )

    return app


def _build_live_loop(
    settings: Settings,
    trace_store: FileTraceStore,
) -> AgentLoop | None:
    if settings.openai_api_key is None or not settings.agent_model.strip():
        return None
    return AgentLoop(
        model_client=OpenAIResponsesClient(
            model=settings.agent_model,
            api_key=settings.openai_api_key.get_secret_value(),
        ),
        tool_router=SpringToolRouter(
            base_url=settings.tool_server_url,
            token=settings.tool_server_token.get_secret_value(),
            timeout_seconds=settings.tool_timeout_seconds,
            max_output_chars=settings.max_tool_output_chars,
        ),
        trace_store=trace_store,
        model=settings.agent_model,
        max_iterations=settings.agent_max_iterations,
        request_timeout_seconds=settings.request_timeout_seconds,
    )


def _status_code(trace: AgentTrace) -> int:
    if trace.status is TraceStatus.COMPLETED:
        return 200
    if trace.error and trace.error.get("code") == "REQUEST_TIMEOUT":
        return 504
    if trace.status is TraceStatus.INCOMPLETE:
        return 409
    return 502


app = create_app()
