import { Gauge, TimerReset } from "lucide-react";
import { formatDuration } from "../lib/format";
import type { AgentTrace } from "../lib/types";

interface CostLatencyPanelProps {
  trace: AgentTrace;
}

export function CostLatencyPanel({ trace }: CostLatencyPanelProps) {
  const costAvailable = trace.estimatedCost != null && trace.pricingMetadata != null;

  return (
    <section className="panel compact-panel" aria-labelledby="runtime-heading">
      <div className="panel-heading">
        <Gauge size={18} aria-hidden="true" />
        <h2 id="runtime-heading">Runtime</h2>
      </div>
      <dl className="runtime-grid">
        <div>
          <dt>Total tokens</dt>
          <dd>{trace.usage.totalTokens ?? "Unavailable"}</dd>
        </div>
        <div>
          <dt>Input / output</dt>
          <dd>
            {trace.usage.inputTokens ?? 0} / {trace.usage.outputTokens ?? 0}
          </dd>
        </div>
        <div>
          <dt>Estimated cost</dt>
          <dd>{costAvailable ? `$${trace.estimatedCost?.toFixed(4)}` : "Cost unavailable"}</dd>
        </div>
        <div>
          <dt>Iterations</dt>
          <dd>{trace.iterations}</dd>
        </div>
      </dl>
      <div className="latency-line">
        <TimerReset size={16} aria-hidden="true" />
        <span>Trace duration {formatDuration(trace.totalDurationMs)}</span>
      </div>
    </section>
  );
}
