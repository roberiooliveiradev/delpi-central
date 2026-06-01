import type { AdminQualityReport, AdminQualityIssue } from "../../../../data/api/adminTypes";

type AdminQualityOperationsProps = {
  latestReport: AdminQualityReport | null;
  issues: AdminQualityIssue[];
  isLoading?: boolean;
  isGenerating?: boolean;
  onGenerateReport?: () => void;
  onResolveIssue?: (issueId: number) => void;
};

export function AdminQualityOperations({
  latestReport,
  issues,
  isLoading = false,
  isGenerating = false,
  onGenerateReport,
  onResolveIssue,
}: AdminQualityOperationsProps) {
  return (
    <section className="mdc-admin-drawing-metrics" aria-labelledby="mdc-admin-quality-ops-title">
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Playbook 10</p>
          <h3 id="mdc-admin-quality-ops-title">Relatório semanal e issues</h3>
          <p>Geração automática de relatório de qualidade e issues a partir de feedback recorrente.</p>
        </div>
        <button
          type="button"
          className="mdc-admin-btn mdc-admin-btn--primary"
          disabled={isGenerating}
          onClick={onGenerateReport}
        >
          {isGenerating ? "Gerando..." : "Gerar relatório semanal"}
        </button>
      </header>

      {isLoading ? <p className="mdc-chat-muted">Carregando relatório e issues...</p> : null}

      {latestReport ? (
        <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
          <h4>Último relatório #{latestReport.id}</h4>
          <p className="mdc-chat-muted">
            {latestReport.periodStart} → {latestReport.periodEnd}
          </p>
          <pre className="mdc-admin-quality-report__markdown">{latestReport.markdown.slice(0, 1200)}</pre>
        </article>
      ) : (
        <p className="mdc-chat-muted">Nenhum relatório semanal gerado ainda.</p>
      )}

      <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
        <h4>Issues abertas ({issues.length})</h4>
        {issues.length ? (
          <ul>
            {issues.map((issue) => (
              <li key={issue.id}>
                <strong>{issue.title}</strong> — {issue.code}
                {issue.externalUrl ? (
                  <>
                    {" "}
                    <a href={issue.externalUrl} target="_blank" rel="noreferrer">
                      GitHub
                    </a>
                  </>
                ) : null}
                {issue.status === "open" ? (
                  <button
                    type="button"
                    className="mdc-admin-btn mdc-admin-btn--ghost"
                    onClick={() => onResolveIssue?.(issue.id)}
                  >
                    Resolver
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mdc-chat-muted">Nenhuma issue aberta.</p>
        )}
      </article>
    </section>
  );
}
