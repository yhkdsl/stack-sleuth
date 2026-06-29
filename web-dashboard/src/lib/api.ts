import type { AgentTrace, TraceApiError } from "./types";

const DEFAULT_AGENT_API_BASE_URL = "http://localhost:8000";

export function agentApiBaseUrl(): string {
  const configured = import.meta.env.VITE_AGENT_API_BASE_URL;
  return (configured || DEFAULT_AGENT_API_BASE_URL).replace(/\/$/, "");
}

export async function fetchTrace(traceId: string): Promise<AgentTrace> {
  const response = await fetch(
    `${agentApiBaseUrl()}/agent/traces/${encodeURIComponent(traceId)}`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
    },
  );
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = payload as Partial<TraceApiError>;
    throw {
      code: error.code || "TRACE_FETCH_FAILED",
      message: error.message || "Trace could not be loaded.",
      status: response.status,
    } satisfies TraceApiError;
  }
  return payload as AgentTrace;
}
