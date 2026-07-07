import { useState, type ReactNode } from "react";
import { History, Table2 } from "lucide-react";

import type { CommercialProposalHistoryEvent } from "../types/commercial";
import {
  buildHistoryEventKey,
  formatHistoryDateTime,
  formatProcessStageLabel,
  isHistoryEngineeringFlow,
  resolveHistoryDuration,
  resolveHistoryStatus,
} from "../utils/proposalHistoryFormatting";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { CommercialProposalTimeline } from "./CommercialProposalTimeline";
import { DataTable, type DataTableColumn } from "./table";
import { HelpTooltip } from "@delpi/plugin-ui";
import { LoadingActivityCard } from "./LoadingActivityCard";

type HistoryViewMode = "timeline" | "table";

type CommercialProposalHistorySectionProps = {
  items: CommercialProposalHistoryEvent[];
  loading?: boolean;
  exportActions?: ReactNode;
};

function renderEngineeringBadge(event: CommercialProposalHistoryEvent) {
  if (!isHistoryEngineeringFlow(event)) return "—";

  return <span className="dc-history-badge">Engenharia</span>;
}

function renderEventState(event: CommercialProposalHistoryEvent) {
  if (event.is_open) {
    return (
      <span className="dc-history-state dc-history-state--open">
        Em andamento
      </span>
    );
  }

  if (event.is_late) {
    return (
      <span className="dc-history-state dc-history-state--late">Atrasado</span>
    );
  }

  return (
    <span className="dc-history-state dc-history-state--done">Concluído</span>
  );
}

const historyColumns: DataTableColumn<CommercialProposalHistoryEvent>[] = [
  {
    key: "revision",
    header: "Revisão",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.historyRevision,
    render: (row) => row.revision || "—",
    sortable: true,
    sortValue: (row) => row.revision,
  },
  {
    key: "process",
    header: "Processo",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.historyProcess,
    className: "dc-table__col--wide",
    render: (row) =>
      formatProcessStageLabel(row.process_code, row.process_label),
    sortable: true,
    sortValue: (row) => row.process_label ?? row.process_code,
  },
  {
    key: "stage",
    header: "Estágio",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.historyStage,
    className: "dc-table__col--wide",
    render: (row) => formatProcessStageLabel(row.stage_code, row.stage_label),
    sortable: true,
    sortValue: (row) => row.stage_label ?? row.stage_code,
  },
  {
    key: "start",
    header: "Início",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.historyStart,
    className: "dc-table__col--numeric",
    render: (row) => formatHistoryDateTime(row.start_date, row.start_time),
    sortable: true,
    sortValue: (row) => row.start_date,
  },
  {
    key: "limit",
    header: "Limite",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.historyLimit,
    className: "dc-table__col--numeric",
    render: (row) => formatHistoryDateTime(row.limit_date, row.limit_time),
    sortable: true,
    sortValue: (row) => row.limit_date,
  },
  {
    key: "end",
    header: "Encerramento",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.historyEnd,
    className: "dc-table__col--numeric",
    render: (row) =>
      row.is_open
        ? "Em andamento"
        : formatHistoryDateTime(row.end_date, row.end_time),
    sortable: true,
    sortValue: (row) => (row.is_open ? "99999999" : row.end_date),
  },
  {
    key: "duration",
    header: "Duração",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.historyDuration,
    className: "dc-table__col--numeric",
    render: (row) => resolveHistoryDuration(row),
    sortable: true,
    sortValue: (row) => row.duration_minutes,
  },
  {
    key: "status",
    header: "Status",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.historyStatus,
    render: (row) => resolveHistoryStatus(row),
    sortable: true,
    sortValue: (row) => resolveHistoryStatus(row),
  },
  {
    key: "state",
    header: "Situação",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.historyState,
    render: (row) => renderEventState(row),
  },
  {
    key: "engineering",
    header: "Eng.",
    headerHint: COMMERCIAL_HELP_TOOLTIPS.detail.historyEngineering,
    render: (row) => renderEngineeringBadge(row),
  },
];

export function CommercialProposalHistorySection({
  items,
  loading = false,
  exportActions,
}: CommercialProposalHistorySectionProps) {
  const [viewMode, setViewMode] = useState<HistoryViewMode>("timeline");

  if (loading && items.length === 0) {
    return (
      <LoadingActivityCard
        title="Carregando histórico"
        description="Buscando eventos de processo e estágio no TOTVS."
      />
    );
  }

  return (
    <div className="dc-history-section">
      <div className="dc-history-section__toolbar">
        <div
          className="dc-history-section__toggle"
          role="tablist"
          aria-label="Visualização do histórico"
        >
        <button
          type="button"
          role="tab"
          aria-selected={viewMode === "timeline"}
          className={`dc-history-section__toggle-btn${
            viewMode === "timeline"
              ? " dc-history-section__toggle-btn--active"
              : ""
          }`}
          onClick={() => setViewMode("timeline")}
        >
          <History size={16} aria-hidden />
          Linha do tempo
          <HelpTooltip
            content={COMMERCIAL_HELP_TOOLTIPS.detail.historyTimelineView}
            ariaLabel="Ajuda: linha do tempo"
            className="dc-history-section__toggle-help"
          />
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={viewMode === "table"}
          className={`dc-history-section__toggle-btn${
            viewMode === "table" ? " dc-history-section__toggle-btn--active" : ""
          }`}
          onClick={() => setViewMode("table")}
        >
          <Table2 size={16} aria-hidden />
          Tabela
          <HelpTooltip
            content={COMMERCIAL_HELP_TOOLTIPS.detail.historyTableView}
            ariaLabel="Ajuda: tabela"
            className="dc-history-section__toggle-help"
          />
        </button>
        </div>
        {exportActions ? (
          <div className="dc-history-section__export dc-no-print">{exportActions}</div>
        ) : null}
      </div>

      {viewMode === "timeline" ? (
        <CommercialProposalTimeline
          events={items}
          emptyMessage="Nenhum evento de histórico encontrado para esta OV."
        />
      ) : (
        <DataTable
          columns={historyColumns}
          rows={items}
          rowKey={buildHistoryEventKey}
          emptyMessage="Nenhum evento de histórico encontrado para esta OV."
          layout="embedded"
        />
      )}
    </div>
  );
}
