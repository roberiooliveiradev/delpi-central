import { useEffect, useState } from "react";

import {
  getAdminDrawingAnalysisSummary,
  getAdminDocumentVisionSummary,
  getAdminIntentRoutingSummary,
  getAdminInteractivitySummary,
  getAdminTextTaskSummary,
  getAdminLlmCostTable,
  getAdminMetricsTimeseries,
  saveAdminLlmCostTable,
} from "../../../../data/api/adminApi";
import type {
  AdminDrawingAnalysisSummary,
  AdminDocumentVisionSummary,
  AdminIntentRoutingSummary,
  AdminInteractivitySummary,
  AdminTextTaskSummary,
  AdminLlmCostBreakdownItem,
  AdminLlmCostTableEntry,
  AdminMetricsDistributionItem,
  AdminMetricsSummary,
  AdminMetricsTimeseriesResponse,
} from "../../../../data/api/adminTypes";
import { AdminDrawingAnalysisMetrics } from "./AdminDrawingAnalysisMetrics";
import { AdminDocumentVisionMetrics } from "./AdminDocumentVisionMetrics";
import { AdminIntentRoutingMetrics } from "./AdminIntentRoutingMetrics";
import { AdminInteractivityMetrics } from "./AdminInteractivityMetrics";
import { AdminTextTaskMetrics } from "./AdminTextTaskMetrics";
import type { AdminNavState } from "../../../../navigation/adminNavigation";

import "./AdminMetricsTab.css";

type AdminMetricsTabProps = {
  metricsSummary: AdminMetricsSummary | null;
  metricsHours?: number;
  onMetricsHoursChange?: (hours: number) => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  /** Navega para Plataforma → Inteligência (config global do pipeline). */
  onNavigate?: (nav: AdminNavState) => void;
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
    <article className="mdc-admin-kpi-card">
      <h3>{title}</h3>

      {!items || items.length === 0 ? (
        <p>{emptyLabel}</p>
      ) : (
        <ul className="mdc-admin-distribution-list">
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

function CostTablePanel({
  items,
  editable = false,
  onSave,
  isSaving = false,
}: {
  items: AdminLlmCostTableEntry[];
  editable?: boolean;
  onSave?: (entries: AdminLlmCostTableEntry[]) => Promise<void>;
  isSaving?: boolean;
}) {
  const [draft, setDraft] = useState(items);

  useEffect(() => {
    setDraft(items);
  }, [items]);

  return (
    <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
      <h3>Tabela de custo por provider/modelo</h3>
      <p>Valores por 1.000 tokens (prompt e completion). Persistida no banco ou via env.</p>

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
            {draft.map((entry, index) => (
              <tr key={`${entry.provider}-${entry.model}-${index}`}>
                <td>
                  {editable ? (
                    <input
                      value={entry.provider}
                      onChange={(event) => {
                        const next = [...draft];
                        next[index] = { ...entry, provider: event.target.value };
                        setDraft(next);
                      }}
                    />
                  ) : (
                    entry.provider
                  )}
                </td>
                <td>
                  {editable ? (
                    <input
                      value={entry.model}
                      onChange={(event) => {
                        const next = [...draft];
                        next[index] = { ...entry, model: event.target.value };
                        setDraft(next);
                      }}
                    />
                  ) : (
                    entry.model
                  )}
                </td>
                <td>
                  {editable ? (
                    <input
                      type="number"
                      step="0.0001"
                      value={entry.promptCostPer1k}
                      onChange={(event) => {
                        const next = [...draft];
                        next[index] = {
                          ...entry,
                          promptCostPer1k: Number(event.target.value),
                        };
                        setDraft(next);
                      }}
                    />
                  ) : (
                    formatCost(entry.promptCostPer1k)
                  )}
                </td>
                <td>
                  {editable ? (
                    <input
                      type="number"
                      step="0.0001"
                      value={entry.completionCostPer1k}
                      onChange={(event) => {
                        const next = [...draft];
                        next[index] = {
                          ...entry,
                          completionCostPer1k: Number(event.target.value),
                        };
                        setDraft(next);
                      }}
                    />
                  ) : (
                    formatCost(entry.completionCostPer1k)
                  )}
                </td>
                <td>{entry.currency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editable && onSave ? (
        <button
          type="button"
          className="mdc-admin-btn mdc-admin-btn--primary"
          disabled={isSaving}
          onClick={() => void onSave(draft)}
        >
          {isSaving ? "Salvando..." : "Salvar tabela de custo"}
        </button>
      ) : null}
    </article>
  );
}

function CostBreakdownPanel({ items }: { items: AdminLlmCostBreakdownItem[] }) {
  return (
    <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
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

export function AdminMetricsTab({
  metricsSummary,
  metricsHours = 24,
  onMetricsHoursChange,
  onRefresh,
  isRefreshing = false,
  getAccessToken,
  onNavigate,
}: AdminMetricsTabProps) {
  const [timeseries, setTimeseries] = useState<AdminMetricsTimeseriesResponse | null>(null);
  const [costTable, setCostTable] = useState<AdminLlmCostTableEntry[]>([]);
  const [isSavingCostTable, setIsSavingCostTable] = useState(false);
  const [drawingSummary, setDrawingSummary] = useState<AdminDrawingAnalysisSummary | null>(
    null,
  );
  const [isLoadingDrawingSummary, setIsLoadingDrawingSummary] = useState(false);
  const [documentVisionSummary, setDocumentVisionSummary] =
    useState<AdminDocumentVisionSummary | null>(null);
  const [isLoadingDocumentVisionSummary, setIsLoadingDocumentVisionSummary] =
    useState(false);
  const [intentRoutingSummary, setIntentRoutingSummary] =
    useState<AdminIntentRoutingSummary | null>(null);
  const [isLoadingIntentRoutingSummary, setIsLoadingIntentRoutingSummary] =
    useState(false);
  const [textTaskSummary, setTextTaskSummary] = useState<AdminTextTaskSummary | null>(
    null,
  );
  const [isLoadingTextTaskSummary, setIsLoadingTextTaskSummary] = useState(false);
  const [interactivitySummary, setInteractivitySummary] =
    useState<AdminInteractivitySummary | null>(null);
  const [isLoadingInteractivitySummary, setIsLoadingInteractivitySummary] =
    useState(false);

  useEffect(() => {
    if (!getAccessToken || metricsHours <= 24) {
      setTimeseries(null);
      return;
    }

    void getAdminMetricsTimeseries(
      { hours: metricsHours, bucketHours: metricsHours <= 168 ? 24 : 48 },
      { getAccessToken },
    )
      .then(setTimeseries)
      .catch(() => setTimeseries(null));
  }, [getAccessToken, metricsHours]);

  useEffect(() => {
    if (!getAccessToken) {
      return;
    }

    void getAdminLlmCostTable({ getAccessToken })
      .then((response) => setCostTable(response.entries))
      .catch(() => setCostTable(metricsSummary?.advanced?.costTable ?? []));
  }, [getAccessToken, metricsSummary?.advanced?.costTable]);

  useEffect(() => {
    if (!getAccessToken) {
      setDrawingSummary(null);
      return;
    }

    setIsLoadingDrawingSummary(true);

    void getAdminDrawingAnalysisSummary(metricsHours, { getAccessToken })
      .then(setDrawingSummary)
      .catch(() => setDrawingSummary(null))
      .finally(() => setIsLoadingDrawingSummary(false));
  }, [getAccessToken, metricsHours]);

  useEffect(() => {
    if (!getAccessToken) {
      setDocumentVisionSummary(null);
      return;
    }

    setIsLoadingDocumentVisionSummary(true);

    void getAdminDocumentVisionSummary(metricsHours, { getAccessToken })
      .then(setDocumentVisionSummary)
      .catch(() => setDocumentVisionSummary(null))
      .finally(() => setIsLoadingDocumentVisionSummary(false));
  }, [getAccessToken, metricsHours]);

  useEffect(() => {
    if (!getAccessToken) {
      setIntentRoutingSummary(null);
      return;
    }

    setIsLoadingIntentRoutingSummary(true);

    void getAdminIntentRoutingSummary(metricsHours, { getAccessToken })
      .then(setIntentRoutingSummary)
      .catch(() => setIntentRoutingSummary(null))
      .finally(() => setIsLoadingIntentRoutingSummary(false));
  }, [getAccessToken, metricsHours]);

  useEffect(() => {
    if (!getAccessToken) {
      setTextTaskSummary(null);
      return;
    }

    setIsLoadingTextTaskSummary(true);

    void getAdminTextTaskSummary(metricsHours, { getAccessToken })
      .then(setTextTaskSummary)
      .catch(() => setTextTaskSummary(null))
      .finally(() => setIsLoadingTextTaskSummary(false));
  }, [getAccessToken, metricsHours]);

  useEffect(() => {
    if (!getAccessToken) {
      setInteractivitySummary(null);
      return;
    }

    setIsLoadingInteractivitySummary(true);

    void getAdminInteractivitySummary(metricsHours, { getAccessToken })
      .then(setInteractivitySummary)
      .catch(() => setInteractivitySummary(null))
      .finally(() => setIsLoadingInteractivitySummary(false));
  }, [getAccessToken, metricsHours]);

  if (!metricsSummary) {
    return (
      <section className="mdc-admin-metrics-tab">
        <p className="mdc-chat-muted mdc-admin-metrics-tab__loading">Carregando métricas...</p>
      </section>
    );
  }

  const advanced = metricsSummary.advanced;
  const effectiveCostTable =
    costTable.length > 0 ? costTable : (advanced?.costTable ?? []);
  const costBreakdown = advanced?.costBreakdown24h ?? [];
  const windowLabel = metricsSummary.windowHours ?? metricsHours;

  async function handleSaveCostTable(entries: AdminLlmCostTableEntry[]) {
    if (!getAccessToken) {
      return;
    }

    setIsSavingCostTable(true);

    try {
      const response = await saveAdminLlmCostTable(entries, { getAccessToken });
      setCostTable(response.entries);
    } finally {
      setIsSavingCostTable(false);
    }
  }

  return (
    <section className="mdc-admin-metrics-tab">
      <header className="mdc-admin-tab-header mdc-admin-metrics-tab__header">
        <div className="mdc-admin-page-header">
          <p className="mdc-chat-eyebrow">Métricas</p>
          <h2>Observabilidade do Minha DELPI Chat</h2>
          <p>
            Acompanhe uso, erros, ferramentas, custos LLM, assertividade RAG e distribuição por
            agente e usuário.
          </p>
        </div>

        <div className="mdc-admin-metrics-tab__header-actions">
          {onMetricsHoursChange ? (
            <label className="mdc-admin-field mdc-admin-metrics-tab__window">
              <span>Janela</span>
              <select
                value={metricsHours}
                onChange={(event) => onMetricsHoursChange(Number(event.target.value))}
              >
                <option value={24}>24 horas</option>
                <option value={168}>7 dias</option>
                <option value={720}>30 dias</option>
              </select>
            </label>
          ) : null}

          {onRefresh ? (
            <button
              type="button"
              className="mdc-chat-ws-outline-btn"
              disabled={isRefreshing}
              onClick={onRefresh}
            >
              {isRefreshing ? "Atualizando..." : "Atualizar"}
            </button>
          ) : null}
        </div>
      </header>

      {onNavigate ? (
        <aside className="mdc-admin-metrics-tab__intel-callout" role="note">
          <p>
            Toggles de RAG, router de tools e loop agentic foram movidos para{" "}
            <strong>Plataforma → Inteligência</strong> (configuram o pipeline, não são métricas).
          </p>
          <button
            type="button"
            className="mdc-chat-ws-outline-btn"
            onClick={() =>
              onNavigate({ section: "platform", subTab: "intelligence" })
            }
          >
            Abrir inteligência do chat
          </button>
        </aside>
      ) : null}

      <div className="mdc-admin-kpi-grid">
        <article className="mdc-admin-kpi-card">
          <h3>Sessões</h3>
          <strong>{formatNumber(metricsSummary.sessions)}</strong>
          <p>Total de conversas registradas.</p>
        </article>

        <article className="mdc-admin-kpi-card">
          <h3>Mensagens</h3>
          <strong>{formatNumber(metricsSummary.messages)}</strong>
          <p>Total de mensagens armazenadas.</p>
        </article>

        <article className="mdc-admin-kpi-card">
          <h3>Base global</h3>
          <strong>{formatNumber(metricsSummary.activeKnowledgeDocuments)}</strong>
          <p>
            {formatNumber(metricsSummary.knowledgeDocuments)} documento(s),{" "}
            {formatNumber(metricsSummary.knowledgeChunks)} chunk(s).
          </p>
        </article>

        <article className="mdc-admin-kpi-card">
          <h3>Eventos ({windowLabel}h)</h3>
          <strong>{formatNumber(metricsSummary.recentAuditLogs24h)}</strong>
          <p>Total de eventos auditáveis na janela selecionada.</p>
        </article>

        <article className="mdc-admin-kpi-card">
          <h3>Uso de tools</h3>
          <strong>{formatPercent(metricsSummary.toolUsageRate24h)}</strong>
          <p>
            {formatNumber(metricsSummary.recentToolCalls24h)} chamada(s) de ferramenta nas últimas
            24h.
          </p>
        </article>

        <article className="mdc-admin-kpi-card">
          <h3>Taxa de erro</h3>
          <strong>{formatPercent(metricsSummary.errorRate24h)}</strong>
          <p>
            {formatNumber(metricsSummary.recentErrors24h)} erro(s) nas últimas 24h.
          </p>
        </article>

        <article className="mdc-admin-kpi-card">
          <h3>Latência média</h3>
          <strong>{formatNumber(advanced?.latencyAvgMs)}ms</strong>
          <p>{formatNumber(advanced?.instrumentedMessages)} mensagem(ns) instrumentada(s).</p>
        </article>

        <article className="mdc-admin-kpi-card">
          <h3>Tokens estimados</h3>
          <strong>{formatNumber(advanced?.tokensUsed)}</strong>
          <p>Total estimado nas mensagens instrumentadas das últimas 24h.</p>
        </article>

        <article className="mdc-admin-kpi-card">
          <h3>Custo estimado</h3>
          <strong>{formatCost(advanced?.estimatedCost)}</strong>
          <p>Soma das mensagens instrumentadas conforme tabela de custo.</p>
        </article>

        <article className="mdc-admin-kpi-card">
          <h3>Falhas RAG</h3>
          <strong>{formatNumber(advanced?.ragFailures)}</strong>
          <p>Mensagens com RAG ativo, mas sem fontes recuperadas nas últimas 24h.</p>
        </article>

        <article className="mdc-admin-kpi-card">
          <h3>Assertividade RAG</h3>
          <strong>{formatPercent(advanced?.assertivenessRate)}</strong>
          <p>
            {formatNumber(advanced?.ragTestsAssertive24h)} de{" "}
            {formatNumber(advanced?.ragTests24h)} teste(s) assertivo(s) nas últimas 24h.
          </p>
        </article>
      </div>

      <AdminIntentRoutingMetrics
        summary={intentRoutingSummary}
        isLoading={isLoadingIntentRoutingSummary}
        windowHours={windowLabel}
      />

      <AdminInteractivityMetrics
        summary={interactivitySummary}
        isLoading={isLoadingInteractivitySummary}
        windowHours={windowLabel}
      />

      <AdminTextTaskMetrics
        summary={textTaskSummary}
        isLoading={isLoadingTextTaskSummary}
        windowHours={windowLabel}
      />

      <AdminDrawingAnalysisMetrics
        summary={drawingSummary}
        isLoading={isLoadingDrawingSummary}
        windowHours={windowLabel}
      />

      <AdminDocumentVisionMetrics
        summary={documentVisionSummary}
        isLoading={isLoadingDocumentVisionSummary}
        windowHours={windowLabel}
      />

      {effectiveCostTable.length > 0 ? (
        <CostTablePanel
          items={effectiveCostTable}
          editable={Boolean(getAccessToken)}
          isSaving={isSavingCostTable}
          onSave={handleSaveCostTable}
        />
      ) : null}

      {timeseries && timeseries.buckets.length > 0 ? (
        <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
          <h3>Série histórica ({timeseries.windowHours}h)</h3>
          <ul className="mdc-admin-distribution-list mdc-admin-metrics-tab__timeseries">
            {timeseries.buckets.map((bucket) => (
              <li key={bucket.start}>
                <span>
                  {new Date(bucket.start).toLocaleDateString("pt-BR")} —{" "}
                  {formatNumber(bucket.auditLogs)} eventos
                </span>
                <strong>
                  {formatCost(bucket.estimatedCost)} · {formatNumber(bucket.tokensUsed)} tokens
                </strong>
              </li>
            ))}
          </ul>
        </article>
      ) : null}

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

      <article className="mdc-admin-kpi-card">
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
