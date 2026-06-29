import type { AgentTrace } from "../lib/types";

export const sampleTrace: AgentTrace = {
  traceId: "trace_sample_null_profile",
  status: "completed",
  startedAt: "2026-06-27T00:00:00Z",
  completedAt: "2026-06-27T00:00:03Z",
  userRequest: "Investigate errors from the last hour and summarize the cause.",
  model: "sample-replay",
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
      arguments: { sql: "SELECT id, account_status, profile_img FROM users WHERE id = 42" },
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
        matches: [
          {
            requestId: "req-demo-4201",
            level: "ERROR",
            message: "NullPointerException in ProfileService while rendering profile_img.",
          },
          {
            requestId: "req-demo-4202",
            level: "ERROR",
            message: "NullPointerException in ProfileService while rendering profile_img.",
          },
          {
            requestId: "req-demo-4203",
            level: "ERROR",
            message: "NullPointerException in ProfileService while rendering profile_img.",
          },
        ],
      },
      errorCode: null,
      latencyMs: 43,
    },
    {
      callId: "call-sql",
      requestId: "req-sql",
      name: "run_read_only_query",
      status: "success",
      output: {
        rowCount: 1,
        rows: [{ id: 42, account_status: "active", profile_img: null }],
      },
      errorCode: null,
      latencyMs: 31,
    },
  ],
  guardrailRejections: [
    {
      callId: "call-drop",
      requestId: "req-drop",
      name: "run_read_only_query",
      status: "rejected",
      output: {
        error: {
          code: "SQL_WRITE_BLOCKED",
          message: "Write statements are blocked by the read-only SQL policy.",
        },
      },
      errorCode: "SQL_WRITE_BLOCKED",
      latencyMs: 4,
    },
  ],
  redactions: [
    {
      path: "$.toolResults[0].output.matches[*].message",
      reason: "log_message_redaction_policy_checked",
    },
  ],
  usage: { inputTokens: 1840, outputTokens: 412, totalTokens: 2252 },
  estimatedCost: null,
  pricingMetadata: null,
  totalDurationMs: 3020,
  persisted: true,
  persistenceError: null,
  confidence: 0.78,
  finalAnswer:
    "Three recent errors point to a NullPointerException in ProfileService. The evidence suggests user 42 has a null profile_img value, and the backend path should handle that nullable field before rendering.",
  error: null,
};
