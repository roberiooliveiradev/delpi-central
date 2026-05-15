import type { AdminMetricsDistributionItem, AdminMetricsSummary } from "../../../../data/api/adminTypes";

import "./AdminMetricsTab.css";

type AdminMetricsTabProps = {
  metricsSummary: AdminMetricsSummary | null;
};

function formatPercent(value?: number): string {
  if (typeof value !== "number") {
    return "0%";
  }

  return `${Math.round(value * 100)}%`;
}

function formatNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

function DistributionList({
  title,
  items,
  emptyLabel,
}: {
  title: string;
  items?: AdminMetricsDistributionItem[];
  emptyLabel: string;
}) {
  return (
    <article className="mdc-admin-metrics-card">
      <h3>{title}</h3>

      {!items || items.length === 0 ? (
        <p>{emptyLabel}</p>
      ) : (
        <ul className="mdc-admin-metrics-tab__distribution">
          {items.map((item) => (
            <li key={item.key}>
              <span>{item.key}</span>
              <strong>{formatNumber(item.count)}</strong>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

export function AdminMetricsTab({ metricsSummary }: AdminMetricsTabProps) {
  if (!metricsSummary) {
    return (
      <section className="mdc-admin-metrics-tab">
        <article className="mdc-admin-metrics-tab__hero">
          <p className="mdc-chat-muted">Carregando métricas...</p>
        </article>
      </section>
    );
  }

  return (
    <section className="mdc-admin-metrics-tab">
      <article className="mdc-admin-metrics-tab__hero">
        <div>
          <p className="mdc-chat-eyebrow">Métricas avançadas</p>
          <h2>Observabilidade do Minha DELPI Chat</h2>
          <p>
            Acompanhe uso, erros, ferramentas e distribuição dos eventos administrativos.
          </p>
        </div>
      </article>

      <div className="mdc-admin-metrics-tab__grid">
        <article className="mdc-admin-metrics-card">
          <h3>Sessões</h3>
          <strong>{formatNumber(metricsSummary.sessions)}</strong>
          <p>Total de conversas registradas.</p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Mensagens</h3>
          <strong>{formatNumber(metricsSummary.messages)}</strong>
          <p>Total de mensagens armazenadas.</p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Base global</h3>
          <strong>{formatNumber(metricsSummary.activeKnowledgeDocuments)}</strong>
          <p>
            {formatNumber(metricsSummary.knowledgeDocuments)} documento(s),{" "}
            {formatNumber(metricsSummary.knowledgeChunks)} chunk(s).
          </p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Eventos 24h</h3>
          <strong>{formatNumber(metricsSummary.recentAuditLogs24h)}</strong>
          <p>Total de eventos auditáveis nas últimas 24h.</p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Uso de tools</h3>
          <strong>{formatPercent(metricsSummary.toolUsageRate24h)}</strong>
          <p>
            {formatNumber(metricsSummary.recentToolCalls24h)} chamada(s) de ferramenta nas últimas 24h.
          </p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Taxa de erro</h3>
          <strong>{formatPercent(metricsSummary.errorRate24h)}</strong>
          <p>
            {formatNumber(metricsSummary.recentErrors24h)} erro(s) nas últimas 24h.
          </p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Latência média</h3>
          <strong>{formatNumber(metricsSummary.advanced?.latencyAvgMs)}ms</strong>
          <p>
            {formatNumber(metricsSummary.advanced?.instrumentedMessages)} mensagem(ns) instrumentada(s).
          </p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Tokens estimados</h3>
          <strong>{formatNumber(metricsSummary.advanced?.tokensUsed)}</strong>
          <p>Total estimado nas mensagens instrumentadas das últimas 24h.</p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Custo estimado</h3>
          <strong>
            {typeof metricsSummary.advanced?.estimatedCost === "number"
              ? `R$ ${metricsSummary.advanced.estimatedCost.toFixed(4)}`
              : "—"}
          </strong>
          <p>Aguardando tabela de custo por provider/modelo.</p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Falhas RAG</h3>
          <strong>{formatNumber(metricsSummary.advanced?.ragFailures)}</strong>
          <p>Mensagens com RAG ativo, mas sem fontes recuperadas nas últimas 24h.</p>
        </article>
      </div>

      <div className="mdc-admin-metrics-tab__columns">
        <DistributionList
          title="Eventos por ação"
          items={metricsSummary.actionDistribution24h}
          emptyLabel="Nenhum evento nas últimas 24h."
        />

        <DistributionList
          title="Eventos por contexto"
          items={metricsSummary.contextDistribution24h}
          emptyLabel="Nenhum contexto registrado nas últimas 24h."
        />

        <DistributionList
          title="Erros por ação"
          items={metricsSummary.errorDistribution24h}
          emptyLabel="Nenhum erro registrado nas últimas 24h."
        />
      </div>

      <article className="mdc-admin-metrics-card">
        <h3>Próximas instrumentações</h3>

        {metricsSummary.advanced?.notes?.length ? (
          <ul className="mdc-admin-metrics-tab__notes">
            {metricsSummary.advanced.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        ) : (
          <p>Sem observações adicionais.</p>
        )}
      </article>
    </section>
  );
}
