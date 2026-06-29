import { FileSearch } from "lucide-react";

export function EmptyState() {
  return (
    <main className="app-shell centered-shell">
      <section className="panel empty-state">
        <FileSearch size={26} aria-hidden="true" />
        <h1>No trace selected</h1>
        <p>Open a persisted trace by URL, or inspect the bundled replay trace without an API key.</p>
        <a className="primary-link" href="/replay">
          Open sample replay
        </a>
      </section>
    </main>
  );
}
