import { useEffect, useMemo, useState } from "react";
import { CostLatencyPanel } from "./components/CostLatencyPanel";
import { EmptyState } from "./components/EmptyState";
import { ErrorState } from "./components/ErrorState";
import { EvidenceTable } from "./components/EvidenceTable";
import { FinalAnswerPanel } from "./components/FinalAnswerPanel";
import { GuardrailPanel } from "./components/GuardrailPanel";
import { RawTraceViewer } from "./components/RawTraceViewer";
import { RedactionPanel } from "./components/RedactionPanel";
import { TraceHeader } from "./components/TraceHeader";
import { TraceTimeline } from "./components/TraceTimeline";
import { sampleTrace } from "./data/sampleTrace";
import { fetchTrace } from "./lib/api";
import type { AgentTrace, TraceApiError } from "./lib/types";
import "./styles.css";

type Route =
  | { name: "index" }
  | { name: "replay" }
  | { name: "trace"; traceId: string }
  | { name: "not-found" };

function routeFromPath(pathname: string): Route {
  if (pathname === "/" || pathname === "/traces") return { name: "index" };
  if (pathname === "/replay") return { name: "replay" };
  const traceMatch = pathname.match(/^\/traces\/([^/]+)$/);
  if (traceMatch) return { name: "trace", traceId: decodeURIComponent(traceMatch[1]) };
  return { name: "not-found" };
}

function TracePage({ trace, modeLabel }: { trace: AgentTrace; modeLabel: string }) {
  return (
    <main className="app-shell">
      <TraceHeader trace={trace} modeLabel={modeLabel} />
      <div className="dashboard-grid">
        <TraceTimeline trace={trace} />
        <aside className="side-rail">
          <FinalAnswerPanel answer={trace.finalAnswer} />
          <CostLatencyPanel trace={trace} />
          <GuardrailPanel rejections={trace.guardrailRejections} />
          <RedactionPanel redactions={trace.redactions} />
        </aside>
      </div>
      <EvidenceTable trace={trace} />
      <RawTraceViewer trace={trace} />
    </main>
  );
}

function TraceLoader({ traceId }: { traceId: string }) {
  const [trace, setTrace] = useState<AgentTrace | null>(null);
  const [error, setError] = useState<TraceApiError | null>(null);

  useEffect(() => {
    let cancelled = false;
    setTrace(null);
    setError(null);
    fetchTrace(traceId)
      .then((payload) => {
        if (!cancelled) setTrace(payload);
      })
      .catch((caught: TraceApiError) => {
        if (!cancelled) {
          setError({
            code: caught.code || "TRACE_FETCH_FAILED",
            message: caught.message || "Trace could not be loaded.",
            status: caught.status || 0,
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [traceId]);

  if (error) return <ErrorState error={error} />;
  if (!trace) {
    return (
      <main className="app-shell centered-shell">
        <section className="panel loading-panel">Loading trace {traceId}...</section>
      </main>
    );
  }
  return <TracePage trace={trace} modeLabel="Persisted trace" />;
}

export default function App() {
  const route = useMemo(() => routeFromPath(window.location.pathname), []);

  if (route.name === "replay") return <TracePage trace={sampleTrace} modeLabel="Sample replay" />;
  if (route.name === "trace") return <TraceLoader traceId={route.traceId} />;
  if (route.name === "index") return <EmptyState />;
  return (
    <ErrorState
      error={{
        code: "ROUTE_NOT_FOUND",
        message: "Use /traces, /traces/{traceId}, or /replay.",
        status: 404,
      }}
    />
  );
}
