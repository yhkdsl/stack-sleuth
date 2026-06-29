import { Activity, Clock3, DatabaseZap } from "lucide-react";
import { formatDuration, formatTimestamp, titleCase } from "../lib/format";
import type { AgentTrace } from "../lib/types";

interface TraceHeaderProps {
  trace: AgentTrace;
  modeLabel: string;
}

export function TraceHeader({ trace, modeLabel }: TraceHeaderProps) {
  return (
    <header className="trace-header">
      <div className="eyebrow-row">
        <span className="mode-pill">{modeLabel}</span>
        <span className={`status-pill status-${trace.status}`}>{titleCase(trace.status)}</span>
      </div>
      <div className="header-grid">
        <div>
          <p className="section-kicker">Original request</p>
          <h1>{trace.userRequest}</h1>
        </div>
        <dl className="metric-strip" aria-label="Trace summary">
          <div>
            <Activity size={17} aria-hidden="true" />
            <dt>Trace</dt>
            <dd>{trace.traceId}</dd>
          </div>
          <div>
            <DatabaseZap size={17} aria-hidden="true" />
            <dt>Model</dt>
            <dd>{trace.model}</dd>
          </div>
          <div>
            <Clock3 size={17} aria-hidden="true" />
            <dt>Duration</dt>
            <dd>{formatDuration(trace.totalDurationMs)}</dd>
          </div>
        </dl>
      </div>
      <p className="timestamp-line">
        Started {formatTimestamp(trace.startedAt)} · Completed {formatTimestamp(trace.completedAt)}
      </p>
    </header>
  );
}
