import { useMemo, useState } from "react";
import { History, Table2 } from "lucide-react";

import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { DataTableColumn } from "./DataTable";
import { DataTable } from "./DataTable";
import { HelpTooltip } from "./HelpTooltip";
import { LmpHistoryTimeline } from "./LmpHistoryTimeline";
import type { LmpHistoryEvent } from "../types/lmp";
import {
  buildHistoryEventKey,
  formatHistoryDateTime,
  formatProcessStageLabel,
  isHistoryEngineeringFlow,
  resolveHistoryDuration,
  resolveHistoryStatus,
  summarizeHistoryEvents,
} from "../utils/historyFormatting";

type HistoryViewMode = "timeline" | "table";

type LmpHistorySectionProps = {
  events: LmpHistoryEvent[];
};

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

export function LmpHistorySection({ events }: LmpHistorySectionProps) {
  const [viewMode, setViewMode] = useState<HistoryViewMode>("timeline");
  const summary = useMemo(() => summarizeHistoryEvents(events), [events]);

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

      {viewMode === "timeline" ? (
        <LmpHistoryTimeline events={events} />
      ) : (
        <DataTable
          columns={historyColumns}
          rows={events}
          rowKey={buildHistoryEventKey}
          emptyMessage="Nenhum evento registrado no histórico da OV."
          getRowClassName={(row) =>
            row.is_current ? "lmps-table__row--current" : undefined
          }
        />
      )}
    </section>
  );
}
