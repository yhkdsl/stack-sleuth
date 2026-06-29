import { TriangleAlert } from "lucide-react";
import type { TraceApiError } from "../lib/types";

interface ErrorStateProps {
  error: TraceApiError;
}

export function ErrorState({ error }: ErrorStateProps) {
  return (
    <main className="app-shell centered-shell">
      <section className="panel error-state">
        <TriangleAlert size={26} aria-hidden="true" />
        <h1>Trace unavailable</h1>
        <p>{error.message}</p>
        <code>{error.code}</code>
      </section>
    </main>
  );
}
