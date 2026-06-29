import { Braces } from "lucide-react";
import { compactJson } from "../lib/format";
import type { AgentTrace } from "../lib/types";

interface RawTraceViewerProps {
  trace: AgentTrace;
}

export function RawTraceViewer({ trace }: RawTraceViewerProps) {
  return (
    <section className="panel raw-panel" aria-labelledby="raw-trace-heading">
      <div className="panel-heading">
        <Braces size={18} aria-hidden="true" />
        <h2 id="raw-trace-heading">Raw trace</h2>
      </div>
      <details>
        <summary>Inspect sanitized JSON</summary>
        <pre>{compactJson(trace)}</pre>
      </details>
    </section>
  );
}
