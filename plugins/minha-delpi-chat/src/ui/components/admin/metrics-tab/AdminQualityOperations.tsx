import type { AdminQualityReport, AdminQualityIssue } from "../../../../data/api/adminTypes";
import { AdminMetricSection } from "../shared/AdminMetricSection";

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
    <AdminMetricSection
      id="mdc-admin-quality-ops-title"
      domain="Qualidade"
      title="Relatório semanal e pendências"
      description="Geração automática de relatório de qualidade e pendências a partir de feedback recorrente."
      isLoading={isLoading}
      loadingMessage="Carregando relatório e pendências..."
    >
      <div className="mdc-admin-metric-section__toolbar">
        <button
          type="button"
          className="mdc-admin-btn mdc-admin-btn--primary"
          disabled={isGenerating}
          onClick={onGenerateReport}
        >
          {isGenerating ? "Gerando..." : "Gerar relatório semanal"}
        </button>
      </div>

      {latestReport ? (
        <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
          <h4>Último relatório #{latestReport.id}</h4>
          <p className="mdc-chat-muted">
            {latestReport.periodStart} → {latestReport.periodEnd}
          </p>
          <pre className="mdc-admin-quality-report__markdown">{latestReport.markdown.slice(0, 1200)}</pre>
        </article>
      ) : null}

      <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
        <h4>Pendências abertas ({issues.length})</h4>
        {issues.length ? (
          <ul>
            {issues.map((issue) => (
              <li key={issue.id}>
                <strong>{issue.title}</strong> — {issue.code}
                {issue.externalUrl ? (
                  <>
                    {" "}
                    <a href={issue.externalUrl} target="_blank" rel="noreferrer">
                      Abrir no GitHub
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
          <p className="mdc-chat-muted">Nenhuma pendência aberta.</p>
        )}
      </article>
    </AdminMetricSection>
  );
}
