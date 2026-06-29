export function formatDuration(ms: number | null): string {
  if (ms == null) return "Unavailable";
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

export function formatTimestamp(value: string | null): string {
  if (!value) return "Unavailable";
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(new Date(value));
}

export function titleCase(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function compactJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}
