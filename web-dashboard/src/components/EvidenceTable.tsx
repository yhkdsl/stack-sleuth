import { TableProperties } from "lucide-react";
import type { AgentTrace } from "../lib/types";

interface EvidenceRow {
  source: string;
  key: string;
  value: string;
}

interface EvidenceTableProps {
  trace: AgentTrace;
}

function rowsFromTrace(trace: AgentTrace): EvidenceRow[] {
  const rows: EvidenceRow[] = [];
  for (const result of trace.toolResults) {
    const output = result.output;
    if (Array.isArray(output.matches)) {
      for (const match of output.matches as Array<Record<string, unknown>>) {
        rows.push({
          source: result.name,
          key: String(match.requestId || match.level || "match"),
          value: String(match.message || JSON.stringify(match)),
        });
      }
    }
    if (Array.isArray(output.rows)) {
      for (const row of output.rows as Array<Record<string, unknown>>) {
        for (const [key, value] of Object.entries(row)) {
          rows.push({ source: result.name, key, value: String(value) });
        }
      }
    }
    if (typeof output.status === "string") {
      rows.push({ source: result.name, key: "status", value: output.status });
    }
  }
  return rows;
}

export function EvidenceTable({ trace }: EvidenceTableProps) {
  const evidence = rowsFromTrace(trace);

  return (
    <section className="panel evidence-panel" aria-labelledby="evidence-heading">
      <div className="panel-heading">
        <TableProperties size={18} aria-hidden="true" />
        <h2 id="evidence-heading">Evidence</h2>
      </div>
      {evidence.length === 0 ? (
        <p className="muted">No structured evidence was produced.</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>Key</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {evidence.map((row, index) => (
                <tr key={`${row.source}-${row.key}-${index}`}>
                  <td>{row.source}</td>
                  <td>{row.key}</td>
                  <td>{row.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
