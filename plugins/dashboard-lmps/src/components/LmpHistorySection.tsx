import { useEffect, useMemo, useState } from "react";
import { History, Table2 } from "lucide-react";

import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { DataTableColumn } from "./DataTable";
import { DataTable } from "./DataTable";
import { HelpTooltip } from "@delpi/plugin-ui";
import { LmpHistoryTimeline } from "./LmpHistoryTimeline";
import type { LmpHistoryEvent } from "../types/lmp";
import {
  buildHistoryEventKey,
  filterHistoryEvents,
  formatHistoryDateTime,
  formatProcessStageLabel,
  isHistoryEngineeringFlow,
  resolveHistoryDuration,
  resolveHistoryStatus,
  summarizeHistoryEvents,
  type HistoryEventFilter,
} from "../utils/historyFormatting";
import {
  readHistoryEventFilter,
  readHistoryViewMode,
  writeHistoryEventFilter,
  writeHistoryViewMode,
  type HistoryViewMode,
} from "../utils/historyPreferences";

type LmpHistorySectionProps = {
  events: LmpHistoryEvent[];
  referenceRevision?: string | null;
  panelStartDate?: string | null;
};

const HISTORY_FILTERS: Array<{
  id: HistoryEventFilter;
  label: string;
  hint: string;
}> = [
  {
    id: "all",
    label: "Todos",
    hint: LMPS_HELP_TOOLTIPS.detail.historyFilterAll,
  },
  {
    id: "engineering",
    label: "Engenharia",
    hint: LMPS_HELP_TOOLTIPS.detail.historyFilterEngineering,
  },
  {
    id: "open",
    label: "Em aberto",
    hint: LMPS_HELP_TOOLTIPS.detail.historyFilterOpen,
  },
  {
    id: "current_revision",
    label: "Revisão atual",
    hint: LMPS_HELP_TOOLTIPS.detail.historyFilterCurrentRevision,
  },
];

function renderEngineeringBadge(event: LmpHistoryEvent) {
  if (!isHistoryEngineeringFlow(event)) return "—";

  return <span className="lmps-history-badge">Engenharia</span>;
}

function renderEventState(event: LmpHistoryEvent) {
  if (event.is_open) {
    return (
      <span className="lmps-history-state lmps-history-state--open">Em andamento</span>
    );
  }

  if (event.is_late) {
    return <span className="lmps-history-state lmps-history-state--late">Atrasado</span>;
  }

  return <span className="lmps-history-state lmps-history-state--done">Concluído</span>;
}

const historyColumns: DataTableColumn<LmpHistoryEvent>[] = [
  {
    key: "revision",
    header: "Revisão",
    headerHint: LMPS_HELP_TOOLTIPS.detail.historyRevision,
    render: (row) => row.revision || "—",
  },
  {
    key: "process",
    header: "Processo",
    headerHint: LMPS_HELP_TOOLTIPS.detail.historyProcess,
    className: "lmps-table__col--wide",
    render: (row) => formatProcessStageLabel(row.process_code, row.process_label),
  },
  {
    key: "stage",
    header: "Estágio",
    headerHint: LMPS_HELP_TOOLTIPS.detail.historyStage,
    className: "lmps-table__col--wide",
    render: (row) => formatProcessStageLabel(row.stage_code, row.stage_label),
  },
  {
    key: "start",
    header: "Início",
    headerHint: LMPS_HELP_TOOLTIPS.detail.historyStart,
    render: (row) => formatHistoryDateTime(row.start_date, row.start_time),
  },
  {
    key: "limit",
    header: "Limite",
    headerHint: LMPS_HELP_TOOLTIPS.detail.historyLimit,
    render: (row) => formatHistoryDateTime(row.limit_date, row.limit_time),
  },
  {
    key: "end",
    header: "Encerramento",
    headerHint: LMPS_HELP_TOOLTIPS.detail.historyEnd,
    render: (row) =>
      row.is_open
        ? "Em andamento"
        : formatHistoryDateTime(row.end_date, row.end_time),
  },
  {
    key: "duration",
    header: "Duração",
    headerHint: LMPS_HELP_TOOLTIPS.detail.historyDuration,
    render: (row) => resolveHistoryDuration(row),
  },
  {
    key: "status",
    header: "Status",
    headerHint: LMPS_HELP_TOOLTIPS.detail.historyStatus,
    render: (row) => resolveHistoryStatus(row),
  },
  {
    key: "state",
    header: "Situação",
    headerHint: LMPS_HELP_TOOLTIPS.detail.historyState,
    render: (row) => renderEventState(row),
  },
  {
    key: "engineering",
    header: "Fluxo",
    headerHint: LMPS_HELP_TOOLTIPS.detail.historyEngineering,
    render: (row) => renderEngineeringBadge(row),
  },
];

export function LmpHistorySection({
  events,
  referenceRevision,
  panelStartDate,
}: LmpHistorySectionProps) {
  const historyReferenceRevision = referenceRevision?.trim() || null;
  const historyPanelStartDate = panelStartDate?.trim() || null;

  const [viewMode, setViewMode] = useState<HistoryViewMode>(() => readHistoryViewMode());
  const [eventFilter, setEventFilter] = useState<HistoryEventFilter>(() =>
    readHistoryEventFilter(),
  );

  useEffect(() => {
    writeHistoryViewMode(viewMode);
  }, [viewMode]);

  useEffect(() => {
    writeHistoryEventFilter(eventFilter);
  }, [eventFilter]);

  const panelScopeOptions = useMemo(
    () => ({
      referenceRevision: historyReferenceRevision,
      panelStartDate: historyPanelStartDate,
    }),
    [historyReferenceRevision, historyPanelStartDate],
  );

  const filteredEvents = useMemo(
    () => filterHistoryEvents(events, eventFilter, panelScopeOptions),
    [events, eventFilter, panelScopeOptions],
  );

  const summary = useMemo(
    () => summarizeHistoryEvents(filteredEvents, { totalCount: events.length }),
    [filteredEvents, events.length],
  );

  const usesPanelScope = eventFilter !== "all";

  const revisionContextMessage = useMemo(() => {
    if (!usesPanelScope) {
      return null;
    }

    const scopeParts: string[] = [];
    if (historyReferenceRevision) {
      scopeParts.push(`revisão ${historyReferenceRevision}`);
    }
    if (historyPanelStartDate && historyPanelStartDate.length === 8) {
      scopeParts.push(
        `a partir de ${historyPanelStartDate.slice(6, 8)}/${historyPanelStartDate.slice(4, 6)}/${historyPanelStartDate.slice(0, 4)}`,
      );
    }

    if (scopeParts.length === 0) {
      return null;
    }

    const scopeLabel = scopeParts.join(", ");

    if (filteredEvents.length > 0) {
      return `Histórico alinhado ao painel LMP (${scopeLabel}). Use «Todos» para ver revisões anteriores.`;
    }

    if (events.length === 0) {
      return null;
    }

    return `Nenhum evento AIJ010 no escopo do painel (${scopeLabel}). Use «Todos» para consultar o histórico completo da OV.`;
  }, [
    usesPanelScope,
    historyReferenceRevision,
    historyPanelStartDate,
    filteredEvents.length,
    events.length,
  ]);

  const emptyMessage =
    events.length === 0
      ? "Nenhum evento registrado no histórico da OV."
      : usesPanelScope
        ? "Nenhum evento no escopo do painel LMP para este filtro."
        : "Nenhum evento corresponde ao filtro selecionado.";

  return (
    <section className="lmps-history-section">
      <div className="lmps-history-section__toolbar">
        <p className="lmps-history-section__summary">{summary}</p>

        <div
          className="lmps-history-section__toggle"
          role="tablist"
          aria-label="Visualização do histórico"
        >
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "timeline"}
            className={`lmps-history-section__toggle-btn${
              viewMode === "timeline" ? " lmps-history-section__toggle-btn--active" : ""
            }`}
            onClick={() => setViewMode("timeline")}
          >
            <History size={16} aria-hidden="true" />
            Linha do tempo
            <HelpTooltip
              content={LMPS_HELP_TOOLTIPS.detail.historyTimelineView}
              ariaLabel="Ajuda: linha do tempo"
              className="lmps-history-section__toggle-help"
            />
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "table"}
            className={`lmps-history-section__toggle-btn${
              viewMode === "table" ? " lmps-history-section__toggle-btn--active" : ""
            }`}
            onClick={() => setViewMode("table")}
          >
            <Table2 size={16} aria-hidden="true" />
            Tabela
            <HelpTooltip
              content={LMPS_HELP_TOOLTIPS.detail.historyTableView}
              ariaLabel="Ajuda: tabela"
              className="lmps-history-section__toggle-help"
            />
          </button>
        </div>
      </div>

      <div className="lmps-history-section__filters" role="group" aria-label="Filtros do histórico">
        {HISTORY_FILTERS.map((filter) => (
          <div key={filter.id} className="lmps-history-section__filter-item">
            <button
              type="button"
              className={`lmps-history-section__filter-btn${
                eventFilter === filter.id ? " lmps-history-section__filter-btn--active" : ""
              }`}
              aria-pressed={eventFilter === filter.id}
              onClick={() => setEventFilter(filter.id)}
            >
              {filter.label}
            </button>
            <HelpTooltip
              content={filter.hint}
              ariaLabel={`Ajuda: filtro ${filter.label}`}
              className="lmps-history-section__filter-help"
            />
          </div>
        ))}
      </div>

      {revisionContextMessage ? (
        <p className="lmps-history-section__context">{revisionContextMessage}</p>
      ) : null}

      {viewMode === "timeline" ? (
        <LmpHistoryTimeline events={filteredEvents} emptyMessage={emptyMessage} />
      ) : (
        <DataTable
          columns={historyColumns}
          rows={filteredEvents}
          rowKey={buildHistoryEventKey}
          emptyMessage={emptyMessage}
          getRowClassName={(row) =>
            row.is_current ? "lmps-table__row--current" : undefined
          }
        />
      )}
    </section>
  );
}
