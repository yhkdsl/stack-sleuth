import { render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const tracePayload = {
  traceId: "trace_ui_123",
  status: "completed",
  startedAt: "2026-06-27T00:00:00Z",
  completedAt: "2026-06-27T00:00:01Z",
  userRequest: "Investigate recent errors",
  model: "test-model",
  iterations: 2,
  toolCalls: [
    {
      callId: "call-logs",
      requestId: "req-logs",
      name: "search_error_logs",
      arguments: { keyword: "ERROR", sinceMinutes: 60, limit: 20 },
      iteration: 1,
    },
    {
      callId: "call-sql",
      requestId: "req-sql",
      name: "run_read_only_query",
      arguments: { sql: "SELECT id, profile_img FROM users WHERE id = 42" },
      iteration: 2,
    },
  ],
  toolResults: [
    {
      callId: "call-logs",
      requestId: "req-logs",
      name: "search_error_logs",
      status: "success",
      output: {
        matchCount: 3,
        matches: [{ requestId: "req-demo-4201", message: "[REDACTED]" }],
      },
      errorCode: null,
      latencyMs: 12,
    },
    {
      callId: "call-sql",
      requestId: "req-sql",
      name: "run_read_only_query",
      status: "success",
      output: {
        rowCount: 1,
        rows: [{ id: 42, profile_img: null, account_status: "active" }],
      },
      errorCode: null,
      latencyMs: 18,
    },
  ],
  guardrailRejections: [
    {
      callId: "call-drop",
      requestId: "req-drop",
      name: "run_read_only_query",
      status: "rejected",
      output: { error: { code: "SQL_WRITE_BLOCKED", message: "Write statements are blocked." } },
      errorCode: "SQL_WRITE_BLOCKED",
      latencyMs: 2,
    },
  ],
  redactions: [{ path: "$.toolResults[0].output.matches[0].message", reason: "pii_pattern" }],
  usage: { inputTokens: 12, outputTokens: 5, totalTokens: 17 },
  estimatedCost: null,
  pricingMetadata: null,
  totalDurationMs: 1000,
  persisted: true,
  persistenceError: null,
  confidence: 0.72,
  finalAnswer: "Three recent errors point to a null profile image.",
  error: null,
};

function setPath(pathname: string) {
  window.history.pushState({}, "", pathname);
}

describe("Trace dashboard", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    setPath("/replay");
  });

  it("renders sample replay without calling the agent API", () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");

    render(<App />);

    expect(screen.getByText("Sample replay")).toBeInTheDocument();
    expect(screen.getAllByText(/NullPointerException/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("search_error_logs").length).toBeGreaterThan(0);
    expect(screen.getByText("Guardrail review")).toBeInTheDocument();
    expect(screen.getAllByText("SQL_WRITE_BLOCKED").length).toBeGreaterThan(0);
    expect(screen.getByText("Cost unavailable")).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("fetches trace details from FastAPI only", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => tracePayload,
    });
    vi.stubGlobal("fetch", fetchMock);
    setPath("/traces/trace_ui_123");

    render(<App />);

    await screen.findByText("Three recent errors point to a null profile image.");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toContain("/agent/traces/trace_ui_123");
    expect(fetchMock.mock.calls[0][0]).not.toContain("/internal/tools");
  });

  it("labels redacted fields and renders evidence", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => tracePayload,
    });
    vi.stubGlobal("fetch", fetchMock);
    setPath("/traces/trace_ui_123");

    render(<App />);

    const redactions = await screen.findByRole("region", { name: "Redactions" });
    expect(within(redactions).getByText("$.toolResults[0].output.matches[0].message")).toBeInTheDocument();
    expect(screen.getByText("req-demo-4201")).toBeInTheDocument();
    expect(screen.getByText("profile_img")).toBeInTheDocument();
  });

  it("shows a missing trace error state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ code: "TRACE_NOT_FOUND", message: "Trace was not found." }),
      }),
    );
    setPath("/traces/missing-trace");

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Trace unavailable")).toBeInTheDocument();
    });
    expect(screen.getByText("TRACE_NOT_FOUND")).toBeInTheDocument();
  });

  it("shows the trace index empty state", () => {
    setPath("/traces");

    render(<App />);

    expect(screen.getByText("No trace selected")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open sample replay" })).toHaveAttribute("href", "/replay");
  });
});
