import { useEffect, useMemo, useState } from "react";
import type {
  StrategicIndicatorsAuditEntityKey,
  StrategicIndicatorsSettingsAuditItem,
} from "../../data/types/settingsAudit";
import "./AuditTimelinePanel.css";
import { SiSelectControl } from "./siFiltersUi";
import { SiNativeTextControl } from "./siNativeFormFields";

type AuditTimelinePanelProps = {
  items: StrategicIndicatorsSettingsAuditItem[];
  loading: boolean;
  error: string | null;
  initialEntityKey: "all" | StrategicIndicatorsAuditEntityKey;
  onEntityKeyChange: (
    value: "all" | StrategicIndicatorsAuditEntityKey,
  ) => void;
  onReload: (params?: {
    limit?: number;
    entityKey?: string;
  }) => void;
};

type AuditFilterValue = "all" | StrategicIndicatorsAuditEntityKey;

const FILTER_OPTIONS: { value: AuditFilterValue; label: string }[] = [
  { value: "all", label: "Todos os blocos" },
  { value: "departments", label: "Departamentos" },
  { value: "department_indicators", label: "Indicadores estruturais" },
  { value: "indicator_goals", label: "Metas anuais" },
  { value: "parameters.global", label: "Parâmetros globais" },
  { value: "governance.notes", label: "Governança" },
  { value: "weights.departments", label: "Pesos por departamento (legado)" },
  { value: "goals.summary", label: "Metas resumidas (legado)" },
];

export function AuditTimelinePanel({
  items,
  loading,
  error,
  initialEntityKey,
  onEntityKeyChange,
  onReload,
}: AuditTimelinePanelProps) {
  const [filter, setFilter] = useState<AuditFilterValue>(initialEntityKey);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [limit, setLimit] = useState("20");
  const hasSearch = search.trim().length > 0;
  const isGeneralView = filter === "all" && !hasSearch;

  function clearEntityFilter() {
    setFilter("all");
    onEntityKeyChange("all");
  }

  function clearSearch() {
    setSearch("");
  }

  function resetAuditView() {
    setSearch("");
    setLimit("20");
    setFilter("all");
    onEntityKeyChange("all");
    setExpandedId(null);
  }

  useEffect(() => {
    void onReload({
      limit: Number(limit),
      entityKey: filter === "all" ? undefined : filter,
    });
  }, [filter, limit, onReload]);

  useEffect(() => {
    setFilter(initialEntityKey);
  }, [initialEntityKey]);

  const filteredItems = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    const base = !normalized
      ? items
      : items.filter((item) => {
          const haystack = [
            item.entity_key,
            item.event_type,
            item.changed_by_email,
            item.changed_by_user_id,
          ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();

          return haystack.includes(normalized);
        });

    return [...base].sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
  }, [items, search]);

  if (loading) {
    return <div className="si-audit-panel">Carregando auditoria...</div>;
  }

  if (error) {
    return (
      <div className="si-audit-panel si-audit-panel--error">
        <div>{error}</div>
        <button
          type="button"
          className="si-audit-panel__button"
          onClick={() =>
            onReload({
              limit: Number(limit),
              entityKey: filter === "all" ? undefined : filter,
            })
          }
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  return (
    <section className="si-audit-panel">
      <div className="si-audit-panel__header">
        <div>
          <h3 className="si-audit-panel__title">Trilha de auditoria</h3>
          <p className="si-audit-panel__subtitle">
            Histórico administrativo recente das alterações do módulo.
          </p>
        </div>

        <div className="si-audit-panel__controls">
          <label className="si-audit-panel__filter">
            <span>Filtrar bloco</span>
            <SiSelectControl
              value={filter}
              onChange={(next) => {
                const nextFilter = next as AuditFilterValue;
                setFilter(nextFilter);
                onEntityKeyChange(nextFilter);
              }}
              options={FILTER_OPTIONS.map((option) => ({
                value: option.value,
                label: option.label,
              }))}
            />
          </label>

          <label className="si-audit-panel__filter">
            <span>Quantidade</span>
            <SiSelectControl
              value={limit}
              onChange={setLimit}
              options={[
                { value: "10", label: "10" },
                { value: "20", label: "20" },
                { value: "50", label: "50" },
                { value: "100", label: "100" },
              ]}
            />
          </label>

          <label className="si-audit-panel__filter si-audit-panel__filter--search">
            <span>Buscar</span>
            <SiNativeTextControl
              type="text"
              value={search}
              onChange={setSearch}
              placeholder="ator, evento ou bloco"
            />
          </label>
        </div>
      </div>

      <div className="si-audit-panel__toolbar">
        <span className="si-audit-panel__toolbar-text">
          {filteredItems.length} evento(s) no resultado atual
        </span>

        <div className="si-audit-panel__toolbar-actions">
          {hasSearch ? (
            <button
              type="button"
              className="si-audit-panel__button si-audit-panel__button--ghost"
              onClick={clearSearch}
            >
              Limpar busca
            </button>
          ) : null}

          <button
            type="button"
            className="si-audit-panel__button si-audit-panel__button--ghost"
            onClick={() => setExpandedId(null)}
            disabled={!expandedId}
          >
            Fechar detalhes
          </button>

          <button
            type="button"
            className="si-audit-panel__button si-audit-panel__button--ghost"
            onClick={resetAuditView}
            disabled={isGeneralView && limit === "20" && !expandedId}
          >
            Voltar ao padrão
          </button>
        </div>
      </div>

      {filter !== "all" ? (
        <div className="si-audit-panel__active-filter">
          <span className="si-audit-panel__active-filter-label">
            Filtro ativo:
          </span>
          <strong className="si-audit-panel__active-filter-value">
            {humanizeEntityKey(filter)}
          </strong>
          <button
            type="button"
            className="si-audit-panel__button si-audit-panel__button--ghost"
            onClick={clearEntityFilter}
          >
            Limpar filtro
          </button>
        </div>
      ) : hasSearch ? (
        <div className="si-audit-panel__active-filter si-audit-panel__active-filter--neutral">
          <span className="si-audit-panel__active-filter-label">
            Busca ativa:
          </span>
          <strong className="si-audit-panel__active-filter-value">
            {search}
          </strong>
          <button
            type="button"
            className="si-audit-panel__button si-audit-panel__button--ghost"
            onClick={clearSearch}
          >
            Limpar busca
          </button>
        </div>
      ) : (
        <div className="si-audit-panel__active-filter si-audit-panel__active-filter--neutral">
          <span className="si-audit-panel__active-filter-label">
            Exibindo:
          </span>
          <strong className="si-audit-panel__active-filter-value">
            Todos os blocos
          </strong>
        </div>
      )}

      {!filteredItems.length ? (
        <div className="si-audit-panel__empty">
          Nenhum evento encontrado para os filtros atuais.
        </div>
      ) : (
        <div className="si-audit-panel__list">
          {filteredItems.map((item, index) => {
            const summary = buildAuditSummary(item);
            const beforeCount = extractItemsCount(item.payload_before);
            const afterCount = extractItemsCount(item.payload_after);
            const isExpanded = expandedId === item.id;
            const isLatest = index === 0;

            return (
              <article key={item.id} className="si-audit-item">
                <div className="si-audit-item__top">
                  <div className="si-audit-item__title-group">
                    <div className="si-audit-item__title-row">
                      <strong className="si-audit-item__entity">
                        {humanizeEntityKey(item.entity_key)}
                      </strong>
                      {isLatest ? (
                        <span className="si-audit-item__latest-badge">
                          Mais recente
                        </span>
                      ) : null}
                    </div>

                    <span className="si-audit-item__entity-key">
                      {item.entity_key}
                    </span>
                  </div>

                  <span className="si-audit-item__event">
                    {humanizeEventType(item.event_type)}
                  </span>
                </div>

                <div className="si-audit-item__meta">
                  <span>
                    Alterado por:{" "}
                    {item.changed_by_email ||
                      item.changed_by_user_id ||
                      "não identificado"}
                  </span>
                  <span>
                    Em: {new Date(item.created_at).toLocaleString("pt-BR")}
                  </span>
                </div>

                <div className="si-audit-item__counts">
                  <span className="si-audit-item__count-badge">
                    Antes: {beforeCount ?? "—"}
                  </span>
                  <span className="si-audit-item__count-badge">
                    Depois: {afterCount ?? "—"}
                  </span>
                </div>

                <div className="si-audit-item__summary">
                  <span className="si-audit-item__summary-label">
                    Resumo da alteração
                  </span>
                  <p className="si-audit-item__summary-text">{summary}</p>
                </div>

                <div className="si-audit-item__actions">
                  <button
                    type="button"
                    className="si-audit-item__toggle"
                    onClick={() =>
                      setExpandedId((current) =>
                        current === item.id ? null : item.id,
                      )
                    }
                  >
                    {isExpanded ? "Ocultar detalhes" : "Ver detalhes"}
                  </button>
                </div>

                {isExpanded ? (
                  <div className="si-audit-item__details">
                    <div className="si-audit-item__payload">
                      <span className="si-audit-item__payload-label">Antes</span>
                      <pre className="si-audit-item__payload-box">
                        {formatPayload(item.payload_before)}
                      </pre>
                    </div>

                    <div className="si-audit-item__payload">
                      <span className="si-audit-item__payload-label">Depois</span>
                      <pre className="si-audit-item__payload-box">
                        {formatPayload(item.payload_after)}
                      </pre>
                    </div>
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function humanizeEntityKey(entityKey: string): string {
  const map: Record<string, string> = {
    "departments": "Departamentos",
    "department_indicators": "Indicadores estruturais",
    "indicator_goals": "Metas anuais",
    "parameters.global": "Parâmetros globais",
    "governance.notes": "Governança",
    "weights.departments": "Pesos por departamento (legado)",
    "goals.summary": "Metas resumidas (legado)",
  };

  return map[entityKey] ?? entityKey;
}

function humanizeEventType(eventType: string): string {
  const map: Record<string, string> = {
    "settings.updated": "Atualização",
  };

  return map[eventType] ?? eventType;
}

function buildAuditSummary(item: StrategicIndicatorsSettingsAuditItem): string {
  const beforeCount = extractItemsCount(item.payload_before);
  const afterCount = extractItemsCount(item.payload_after);

  if (beforeCount === null && afterCount === null) {
    return "Alteração registrada sem resumo estruturado.";
  }

  if (beforeCount === afterCount) {
    return `O bloco manteve ${afterCount ?? 0} item(ns), com atualização de conteúdo.`;
  }

  return `O bloco mudou de ${beforeCount ?? 0} para ${afterCount ?? 0} item(ns).`;
}

function extractItemsCount(
  payload: Record<string, unknown> | null,
): number | null {
  if (!payload) return null;

  const items = payload["items"];
  if (!Array.isArray(items)) return null;

  return items.length;
}

function formatPayload(payload: Record<string, unknown> | null): string {
  if (!payload) return "Sem payload registrado.";
  return JSON.stringify(payload, null, 2);
}