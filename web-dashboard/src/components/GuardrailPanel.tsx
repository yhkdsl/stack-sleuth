import { ShieldAlert } from "lucide-react";
import { compactJson } from "../lib/format";
import type { ToolResultRecord } from "../lib/types";

interface GuardrailPanelProps {
  rejections: ToolResultRecord[];
}

export function GuardrailPanel({ rejections }: GuardrailPanelProps) {
  return (
    <section className="panel guardrail-panel" aria-labelledby="guardrail-heading">
      <div className="panel-heading">
        <ShieldAlert size={18} aria-hidden="true" />
        <h2 id="guardrail-heading">Guardrail review</h2>
      </div>
      {rejections.length === 0 ? (
        <p className="muted">No guardrail rejections in this trace.</p>
      ) : (
        <div className="guardrail-list">
          {rejections.map((rejection) => (
            <article key={rejection.callId} className="guardrail-item">
              <div className="guardrail-item-title">
                <strong>{rejection.errorCode || "REJECTED"}</strong>
                <span>{rejection.name}</span>
              </div>
              <pre>{compactJson(rejection.output)}</pre>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
