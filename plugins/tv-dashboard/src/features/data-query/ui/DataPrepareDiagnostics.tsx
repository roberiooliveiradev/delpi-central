import type { DataQueryDiagnosticDto } from "@delpi/tv-dashboard-presentation";

export function DataPrepareDiagnostics({
  diagnostics,
}: {
  diagnostics: DataQueryDiagnosticDto[];
}) {
  if (diagnostics.length === 0) return null;
  return (
    <section className="td-data-pq__diagnostics" aria-label="Diagnósticos M" aria-live="polite">
      {diagnostics.map((item, index) => (
        <p key={`${item.code}-${index}`} role={item.severity === "error" ? "alert" : "status"}>
          <strong>{item.code}</strong>
          {item.range
            ? ` · L${item.range.startLine}:C${item.range.startColumn}–L${item.range.endLine}:C${item.range.endColumn}`
            : ""}
          {" — "}
          {item.message}
          {item.hint ? ` ${item.hint}` : ""}
        </p>
      ))}
    </section>
  );
}
