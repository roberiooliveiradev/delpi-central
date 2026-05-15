import type { AdminMetricsSummary } from "../../../../data/api/adminTypes";

import "./AdminMetrics.css";

type AdminMetricsProps = {
  metricsSummary: AdminMetricsSummary | null;
};

const METRIC_ITEMS: Array<{
  label: string;
  getValue: (summary: AdminMetricsSummary) => string | number;
}> = [
  {
    label: "Sessões",
    getValue: (summary) => summary.sessions,
  },
  {
    label: "Mensagens",
    getValue: (summary) => summary.messages,
  },
  {
    label: "Documentos globais",
    getValue: (summary) =>
      `${summary.activeKnowledgeDocuments}/${summary.knowledgeDocuments}`,
  },
  {
    label: "Chunks",
    getValue: (summary) => summary.knowledgeChunks,
  },
  {
    label: "Auditorias",
    getValue: (summary) => summary.auditLogs,
  },
  {
    label: "Tools 24h",
    getValue: (summary) => summary.recentToolCalls24h,
  },
  {
    label: "Erros 24h",
    getValue: (summary) => summary.recentErrors24h,
  },
];

export function AdminMetrics({ metricsSummary }: AdminMetricsProps) {
  if (!metricsSummary) {
    return null;
  }

  return (
    <section className="mdc-admin-metrics" aria-label="Resumo operacional">
      {METRIC_ITEMS.map((item) => (
        <article className="mdc-admin-metric-card" key={item.label}>
          <span>{item.label}</span>
          <strong>{item.getValue(metricsSummary)}</strong>
        </article>
      ))}
    </section>
  );
}
