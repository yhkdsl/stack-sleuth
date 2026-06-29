import { Ban, CheckCircle2, CircleAlert, Hourglass, Wrench } from "lucide-react";
import { compactJson, formatDuration } from "../lib/format";
import type { ToolCallRecord, ToolResultRecord } from "../lib/types";

interface ToolCallCardProps {
  call: ToolCallRecord;
  result?: ToolResultRecord;
}

const statusIcon = {
  success: CheckCircle2,
  rejected: Ban,
  failed: CircleAlert,
  timed_out: Hourglass,
};

export function ToolCallCard({ call, result }: ToolCallCardProps) {
  const status = result?.status || "timed_out";
  const Icon = statusIcon[status];

  return (
    <article className={`tool-card tool-card-${status}`}>
      <div className="tool-card-title">
        <span className="tool-index">{call.iteration}</span>
        <Wrench size={16} aria-hidden="true" />
        <h3>{call.name}</h3>
        <span className={`status-pill status-${status}`}>
          <Icon size={14} aria-hidden="true" />
          {status}
        </span>
      </div>
      <dl className="tool-meta">
        <div>
          <dt>Request ID</dt>
          <dd>{call.requestId}</dd>
        </div>
        <div>
          <dt>Latency</dt>
          <dd>{formatDuration(result?.latencyMs ?? null)}</dd>
        </div>
      </dl>
      <details>
        <summary>Arguments</summary>
        <pre>{compactJson(call.arguments)}</pre>
      </details>
      {result ? (
        <details>
          <summary>Result</summary>
          <pre>{compactJson(result.output)}</pre>
        </details>
      ) : null}
    </article>
  );
}
