export type ToolStatus = "success" | "rejected" | "failed" | "timed_out";
export type TraceStatus = "running" | "completed" | "incomplete" | "failed";

export interface ToolCallRecord {
  callId: string;
  requestId: string;
  name: string;
  arguments: Record<string, unknown>;
  iteration: number;
}

export interface ToolResultRecord {
  callId: string;
  requestId: string;
  name: string;
  status: ToolStatus;
  output: Record<string, unknown>;
  errorCode: string | null;
  latencyMs: number;
}

export interface RedactionEvent {
  path: string;
  reason: string;
}

export interface AgentTrace {
  traceId: string;
  status: TraceStatus;
  startedAt: string;
  completedAt: string | null;
  userRequest: string;
  model: string;
  iterations: number;
  toolCalls: ToolCallRecord[];
  toolResults: ToolResultRecord[];
  guardrailRejections: ToolResultRecord[];
  redactions: RedactionEvent[];
  usage: Record<string, number>;
  estimatedCost: number | null;
  pricingMetadata: Record<string, unknown> | null;
  totalDurationMs: number | null;
  persisted: boolean;
  persistenceError: Record<string, string> | null;
  confidence: number | null;
  finalAnswer: string | null;
  error: Record<string, string> | null;
}

export interface TraceApiError {
  code: string;
  message: string;
  status: number;
}
