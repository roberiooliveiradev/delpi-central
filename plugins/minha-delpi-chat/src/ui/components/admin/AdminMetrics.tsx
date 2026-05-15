import type { AdminMetricsSummary } from "../../../data/api/adminTypes";

type AdminMetricsProps = {
  metricsSummary: AdminMetricsSummary | null;
};

export function AdminMetrics({ metricsSummary }: AdminMetricsProps) {
  if (!metricsSummary) {
    return null;
  }

  return (
    <section className="mdc-admin-metrics" aria-label="Resumo operacional">
      <article className="mdc-admin-metric-card">
        <span>Sessões</span>
        <strong>{metricsSummary.sessions}</strong>
      </article>

      <article className="mdc-admin-metric-card">
        <span>Mensagens</span>
        <strong>{metricsSummary.messages}</strong>
      </article>

      <article className="mdc-admin-metric-card">
        <span>Documentos globais</span>
        <strong>
          {metricsSummary.activeKnowledgeDocuments}/{metricsSummary.knowledgeDocuments}
        </strong>
      </article>

      <article className="mdc-admin-metric-card">
        <span>Chunks</span>
        <strong>{metricsSummary.knowledgeChunks}</strong>
      </article>

      <article className="mdc-admin-metric-card">
        <span>Auditorias</span>
        <strong>{metricsSummary.auditLogs}</strong>
      </article>

      <article className="mdc-admin-metric-card">
        <span>Tools 24h</span>
        <strong>{metricsSummary.recentToolCalls24h}</strong>
      </article>

      <article className="mdc-admin-metric-card">
        <span>Erros 24h</span>
        <strong>{metricsSummary.recentErrors24h}</strong>
      </article>
    </section>
  );
}
