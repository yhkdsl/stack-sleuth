import { ListTree } from "lucide-react";
import type { AgentTrace } from "../lib/types";
import { ToolCallCard } from "./ToolCallCard";

interface TraceTimelineProps {
  trace: AgentTrace;
}

export function TraceTimeline({ trace }: TraceTimelineProps) {
  const resultsByCallId = new Map(trace.toolResults.map((result) => [result.callId, result]));

  return (
    <section className="panel timeline-panel" aria-labelledby="timeline-heading">
      <div className="panel-heading">
        <ListTree size={18} aria-hidden="true" />
        <h2 id="timeline-heading">Ordered tool calls</h2>
      </div>
      <div className="timeline-list">
        {trace.toolCalls.map((call) => (
          <ToolCallCard key={call.callId} call={call} result={resultsByCallId.get(call.callId)} />
        ))}
      </div>
    </section>
  );
}
