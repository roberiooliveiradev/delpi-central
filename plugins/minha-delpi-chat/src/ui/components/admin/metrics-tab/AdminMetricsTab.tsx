import type { AdminMetricsSummary } from "../../../../data/api/adminTypes";

import "./AdminMetricsTab.css";

type AdminMetricsTabProps = {
  metricsSummary: AdminMetricsSummary | null;
};

export function AdminMetricsTab({ metricsSummary }: AdminMetricsTabProps) {
  if (!metricsSummary) {
    return (
      <section className="mdc-admin-metrics-tab">
        <p className="mdc-chat-muted">Carregando métricas...</p>
      </section>
    );
  }

  const items = [
    ["Sessões", metricsSummary.sessions],
    ["Mensagens", metricsSummary.messages],
    ["Documentos globais", `${metricsSummary.activeKnowledgeDocuments}/${metricsSummary.knowledgeDocuments}`],
    ["Chunks indexados", metricsSummary.knowledgeChunks],
    ["Auditorias", metricsSummary.auditLogs],
    ["Tools nas últimas 24h", metricsSummary.recentToolCalls24h],
    ["Erros nas últimas 24h", metricsSummary.recentErrors24h],
  ];

  return (
    <section className="mdc-admin-metrics-tab">
      <article className="mdc-admin-metrics-tab__hero">
        <p className="mdc-chat-eyebrow">Indicadores</p>
        <h2>Métricas operacionais</h2>
        <p>
          Visão consolidada do uso do chat, saúde da base de conhecimento,
          auditoria e execução de ferramentas.
        </p>
      </article>

      <div className="mdc-admin-metrics-tab__grid">
        {items.map(([label, value]) => (
          <article key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </div>
    </section>
  );
}
