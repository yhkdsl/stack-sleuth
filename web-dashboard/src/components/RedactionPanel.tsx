import { BadgeCheck } from "lucide-react";
import type { RedactionEvent } from "../lib/types";

interface RedactionPanelProps {
  redactions: RedactionEvent[];
}

export function RedactionPanel({ redactions }: RedactionPanelProps) {
  return (
    <section className="panel compact-panel" aria-label="Redactions">
      <div className="panel-heading">
        <BadgeCheck size={18} aria-hidden="true" />
        <h2>Redactions</h2>
      </div>
      {redactions.length === 0 ? (
        <p className="muted">No redaction events were recorded.</p>
      ) : (
        <ul className="redaction-list">
          {redactions.map((redaction) => (
            <li key={`${redaction.path}-${redaction.reason}`}>
              <code>{redaction.path}</code>
              <span>{redaction.reason}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
