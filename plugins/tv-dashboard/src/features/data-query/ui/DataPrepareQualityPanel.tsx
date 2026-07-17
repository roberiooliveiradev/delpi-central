import type { DataQueryPreview } from "../domain/dataQueryTypes";

export function DataPrepareQualityPanel({
  preview,
  profilingEnabled,
  profilingRequested,
  loading,
  onToggleProfiling,
}: {
  preview: DataQueryPreview | null;
  profilingEnabled: boolean;
  profilingRequested: boolean;
  loading: boolean;
  onToggleProfiling: (enabled: boolean) => void;
}) {
  return (
    <section className="td-data-pq__quality" aria-label="Qualidade e desempenho">
      <div className="td-data-pq__quality-toolbar">
        <strong>Qualidade e desempenho</strong>
        <button
          type="button"
          className="td-btn td-btn--sm td-btn--ghost"
          aria-pressed={profilingRequested}
          disabled={!profilingEnabled || loading}
          onClick={() => onToggleProfiling(!profilingRequested)}
        >
          {profilingRequested ? "Desativar perfil" : "Analisar perfil"}
        </button>
        <span role="status" aria-live="polite">
          {loading
            ? "Analisando…"
            : preview?.profilingStatus === "timeout"
              ? "Perfil cancelado pelo limite de tempo."
              : `${preview?.executionMs ?? 0} ms`}
        </span>
      </div>
      {!profilingEnabled ? (
        <p>Profiling indisponível pelas capabilities.</p>
      ) : null}
      {preview?.columnProfile ? (
        <div className="td-data-pq__quality-columns">
          {preview.columnProfile.columns.map((column) => (
            <article key={column.key} className="td-data-pq__quality-column">
              <strong>{column.key}</strong>
              <span>
                Válidos {column.quality.valid} · Vazios {column.quality.empty} · Erros{" "}
                {column.quality.error}
              </span>
              <span>
                Distintos {column.distribution.distinct} · Repetidos{" "}
                {column.distribution.repeated}
              </span>
              {column.minMaxAvailable ? (
                <span>
                  Mín. {String(column.min)} · Máx. {String(column.max)}
                </span>
              ) : null}
            </article>
          ))}
        </div>
      ) : null}
      {preview?.explainPlan ? (
        <details>
          <summary>Plano de execução ({preview.explainPlan.steps.length} etapas)</summary>
          <ol>
            {preview.explainPlan.steps.map((step) => {
              const metric = preview.stepMetrics?.find(
                (item) => item.stepName === step.name,
              );
              return (
                <li key={step.name}>
                  <code>{step.operation}</code> — {metric?.durationMs ?? 0} ms
                  {step.cost === "potentially_expensive" ? " · operação potencialmente cara" : ""}
                </li>
              );
            })}
          </ol>
        </details>
      ) : null}
    </section>
  );
}
