import type {
  AdminLlmCostBreakdownItem,
  AdminLlmCostTableEntry,
  AdminMetricsDistributionItem,
  AdminMetricsSummary,
} from "../../../../data/api/adminTypes";

import "./AdminMetricsTab.css";

type AdminMetricsTabProps = {
  metricsSummary: AdminMetricsSummary | null;
};

function formatPercent(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return `${Math.round(value * 100)}%`;
}

function formatNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

function formatCost(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return `R$ ${value.toFixed(4)}`;
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
              <span title={item.key}>{item.key}</span>
              <strong>{formatNumber(item.count)}</strong>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

function CostTablePanel({ items }: { items: AdminLlmCostTableEntry[] }) {
  return (
    <article className="mdc-admin-metrics-card mdc-admin-metrics-card--wide">
      <h3>Tabela de custo por provider/modelo</h3>
      <p>Valores por 1.000 tokens (prompt e completion). Configure via LLM_COST_TABLE_JSON.</p>

      <div className="mdc-admin-metrics-tab__table-wrap">
        <table className="mdc-admin-metrics-tab__table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>Modelo</th>
              <th>Prompt / 1K</th>
              <th>Completion / 1K</th>
              <th>Moeda</th>
            </tr>
          </thead>
          <tbody>
            {items.map((entry) => (
              <tr key={`${entry.provider}-${entry.model}`}>
                <td>{entry.provider}</td>
                <td>{entry.model}</td>
                <td>{formatCost(entry.promptCostPer1k)}</td>
                <td>{formatCost(entry.completionCostPer1k)}</td>
                <td>{entry.currency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}

function CostBreakdownPanel({ items }: { items: AdminLlmCostBreakdownItem[] }) {
  return (
    <article className="mdc-admin-metrics-card mdc-admin-metrics-card--wide">
      <h3>Custo estimado por provider/modelo (24h)</h3>
      <p>Agregado a partir das mensagens instrumentadas na auditoria.</p>

      <div className="mdc-admin-metrics-tab__table-wrap">
        <table className="mdc-admin-metrics-tab__table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>Modelo</th>
              <th>Mensagens</th>
              <th>Tokens</th>
              <th>Custo</th>
            </tr>
          </thead>
          <tbody>
            {items.map((entry) => (
              <tr key={`${entry.provider}-${entry.model}`}>
                <td>{entry.provider}</td>
                <td>{entry.model}</td>
                <td>{formatNumber(entry.messages)}</td>
                <td>{formatNumber(entry.tokensUsed)}</td>
                <td>{formatCost(entry.estimatedCost)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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

  const advanced = metricsSummary.advanced;
  const costTable = advanced?.costTable ?? [];
  const costBreakdown = advanced?.costBreakdown24h ?? [];

  return (
    <section className="mdc-admin-metrics-tab">
      <article className="mdc-admin-metrics-tab__hero">
        <div>
          <p className="mdc-chat-eyebrow">Métricas avançadas</p>
          <h2>Observabilidade do Minha DELPI Chat</h2>
          <p>
            Acompanhe uso, erros, ferramentas, custos LLM, assertividade RAG e distribuição por
            agente e usuário.
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
            {formatNumber(metricsSummary.recentToolCalls24h)} chamada(s) de ferramenta nas últimas
            24h.
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
          <strong>{formatNumber(advanced?.latencyAvgMs)}ms</strong>
          <p>{formatNumber(advanced?.instrumentedMessages)} mensagem(ns) instrumentada(s).</p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Tokens estimados</h3>
          <strong>{formatNumber(advanced?.tokensUsed)}</strong>
          <p>Total estimado nas mensagens instrumentadas das últimas 24h.</p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Custo estimado</h3>
          <strong>{formatCost(advanced?.estimatedCost)}</strong>
          <p>Soma das mensagens instrumentadas conforme tabela de custo.</p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Falhas RAG</h3>
          <strong>{formatNumber(advanced?.ragFailures)}</strong>
          <p>Mensagens com RAG ativo, mas sem fontes recuperadas nas últimas 24h.</p>
        </article>

        <article className="mdc-admin-metrics-card">
          <h3>Assertividade RAG</h3>
          <strong>{formatPercent(advanced?.assertivenessRate)}</strong>
          <p>
            {formatNumber(advanced?.ragTestsAssertive24h)} de{" "}
            {formatNumber(advanced?.ragTests24h)} teste(s) assertivo(s) nas últimas 24h.
          </p>
        </article>
      </div>

      {costTable.length > 0 ? <CostTablePanel items={costTable} /> : null}

      {costBreakdown.length > 0 ? <CostBreakdownPanel items={costBreakdown} /> : null}

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

      <div className="mdc-admin-metrics-tab__columns">
        <DistributionList
          title="Mensagens por agente (24h)"
          items={advanced?.agentMetrics}
          emptyLabel="Sem mensagens por agente."
        />

        <DistributionList
          title="Eventos por usuário (24h)"
          items={advanced?.userProfileMetrics}
          emptyLabel="Sem eventos por usuário."
        />
      </div>

      <article className="mdc-admin-metrics-card">
        <h3>Observações</h3>

        {advanced?.notes?.length ? (
          <ul className="mdc-admin-metrics-tab__notes">
            {advanced.notes.map((note) => (
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
