import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Grid2X2, LayoutGrid, LayoutList, Rows3 } from "lucide-react";

import type { DataTableColumn } from "../../components/DataTable";
import { DataTable } from "../../components/DataTable";
import { HelpTooltip } from "@delpi/plugin-ui";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { Pagination } from "../../components/Pagination";
import { ProcessoFormProgress } from "../../components/processo/ProcessoFormProgress";
import { useClientPagination } from "../../hooks/useClientPagination";
import type { Processo } from "../../data/api/transformometroApi";
import { computeProcessoListCompletion } from "../../utils/processoCompletion";
import { renderTableStatus } from "../../utils/tablePresentation";
import { ProcessoFolderIcon } from "./ProcessoFolderIcon";
import {
  pageSizeForProcessoListView,
  PROCESSO_LIST_VIEW_MODES,
  readProcessoListViewMode,
  writeProcessoListViewMode,
  type ProcessoListViewMode,
} from "./processoListViewMode";

type Props = {
  title?: string;
  hint?: string;
  items: Processo[];
  loading?: boolean;
  refreshing?: boolean;
  emptyMessage?: string;
  filters?: ReactNode;
  footer?: ReactNode;
  detailColumns: DataTableColumn<Processo>[];
  onOpen: (processo: Processo) => void;
};

function viewModeIcon(mode: ProcessoListViewMode) {
  switch (mode) {
    case "icons-lg":
      return LayoutGrid;
    case "icons-md":
      return Grid2X2;
    case "list":
      return LayoutList;
    default:
      return Rows3;
  }
}

function folderMeta(processo: Processo): string {
  const stats = processo.setup_stats;
  const parts = [
    processo.familia_processo,
    stats?.instancia_count ? `${stats.instancia_count} melhoria${stats.instancia_count > 1 ? "s" : ""}` : null,
  ].filter(Boolean);
  return parts.join(" · ") || processo.status_processo;
}

export function ProcessoFolderBrowser({
  title = "Processos",
  hint,
  items,
  loading = false,
  refreshing = false,
  emptyMessage = "Nenhum processo encontrado.",
  filters,
  footer,
  detailColumns,
  onOpen,
}: Props) {
  const [viewMode, setViewMode] = useState<ProcessoListViewMode>(() => readProcessoListViewMode());
  const [sortKey, setSortKey] = useState<string>("codigo");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  useEffect(() => {
    writeProcessoListViewMode(viewMode);
  }, [viewMode]);

  const sortedItems = useMemo(() => {
    const copy = [...items];
    copy.sort((left, right) => {
      if (sortKey === "preenchimento") {
        return (
          (computeProcessoListCompletion(left).percent - computeProcessoListCompletion(right).percent) *
          (sortDirection === "asc" ? 1 : -1)
        );
      }
      let leftValue = "";
      let rightValue = "";
      if (sortKey === "codigo") {
        leftValue = left.codigo_processo ?? "";
        rightValue = right.codigo_processo ?? "";
      } else if (sortKey === "status") {
        leftValue = left.status_processo ?? "";
        rightValue = right.status_processo ?? "";
      } else {
        leftValue = left.nome_processo ?? "";
        rightValue = right.nome_processo ?? "";
      }
      const cmp = leftValue.localeCompare(rightValue, "pt-BR", { sensitivity: "base" });
      return sortDirection === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [items, sortDirection, sortKey]);

  const pageSize = pageSizeForProcessoListView(viewMode);
  const { page, setPage, slice, total } = useClientPagination(sortedItems, pageSize);

  function handleSortChange(columnKey: string) {
    if (sortKey === columnKey) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(columnKey);
    setSortDirection("asc");
  }

  const currentMode = PROCESSO_LIST_VIEW_MODES.find((mode) => mode.id === viewMode)!;

  return (
    <section className={`ds-table-section tm-processo-browser${refreshing ? " tm-processo-browser--refreshing" : ""}`}>
      <div className="ds-table-section__header tm-processo-browser__header">
        <div>
          <h2 className="ds-section-title">{title}</h2>
          {hint ? <p className="ds-hint">{hint}</p> : null}
        </div>
        <div className="tm-processo-browser__toolbar">
          <div className="tm-processo-browser__view-modes" role="group" aria-label="Modo de visualização">
            {PROCESSO_LIST_VIEW_MODES.map((mode) => {
              const Icon = viewModeIcon(mode.id);
              const active = viewMode === mode.id;
              return (
                <button
                  key={mode.id}
                  type="button"
                  className={`tm-processo-browser__view-btn${active ? " tm-processo-browser__view-btn--active" : ""}`}
                  aria-pressed={active}
                  title={mode.label}
                  onClick={() => setViewMode(mode.id)}
                >
                  <Icon size={16} aria-hidden="true" />
                  <span>{mode.shortLabel}</span>
                </button>
              );
            })}
          </div>
          <span className="ds-hint tm-processo-browser__count">
            {total} registro{total === 1 ? "" : "s"}
          </span>
        </div>
      </div>

      {filters ? <div className="tm-processo-browser__filters">{filters}</div> : null}

      {loading ? (
        <p className="ds-hint">Carregando processos…</p>
      ) : slice.length === 0 ? (
        <p className="ds-hint">{emptyMessage}</p>
      ) : viewMode === "details" ? (
        <DataTable
          columns={detailColumns}
          rows={slice}
          rowKey={(row) => row.processo_id}
          onRowClick={onOpen}
          sortKey={sortKey}
          sortDirection={sortDirection}
          onSortChange={handleSortChange}
        />
      ) : viewMode === "list" ? (
        <ul className="tm-processo-browser__list" role="list">
          {slice.map((processo) => (
            <li key={processo.processo_id}>
              <button
                type="button"
                className="tm-processo-browser__list-item"
                onClick={() => onOpen(processo)}
              >
                <ProcessoFolderIcon size="sm" />
                <span className="tm-processo-browser__list-main">
                  <span className="tm-processo-browser__list-title">{processo.nome_processo}</span>
                  <span className="tm-processo-browser__list-meta">
                    {processo.codigo_processo} · {folderMeta(processo)}
                  </span>
                </span>
                <span className="tm-processo-browser__list-status">{renderTableStatus(processo.status_processo)}</span>
                <ProcessoFormProgress
                  compact
                  completion={computeProcessoListCompletion(processo)}
                  title={`Preenchimento — ${processo.codigo_processo}`}
                />
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <div
          className={
            viewMode === "icons-lg"
              ? "tm-processo-browser__grid tm-processo-browser__grid--lg"
              : "tm-processo-browser__grid tm-processo-browser__grid--md"
          }
          role="list"
        >
          {slice.map((processo) => (
            <article key={processo.processo_id} className="tm-processo-folder" role="listitem">
              <button
                type="button"
                className="tm-processo-folder__open"
                onClick={() => onOpen(processo)}
                title={`Abrir ${processo.codigo_processo}`}
              >
                <ProcessoFolderIcon size={viewMode === "icons-lg" ? "lg" : "md"} />
                <span className="tm-processo-folder__code">{processo.codigo_processo}</span>
                <span className="tm-processo-folder__name">{processo.nome_processo}</span>
                <span className="tm-processo-folder__meta">{folderMeta(processo)}</span>
                <span className="tm-processo-folder__status">{renderTableStatus(processo.status_processo)}</span>
                <ProcessoFormProgress
                  compact
                  completion={computeProcessoListCompletion(processo)}
                  title={`Preenchimento — ${processo.codigo_processo}`}
                />
              </button>
            </article>
          ))}
        </div>
      )}

      <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />

      {footer ? <div className="tm-processo-browser__footer">{footer}</div> : null}

      <p className="ds-hint tm-processo-browser__mode-hint">
        Visualização: {currentMode.label}. Clique na pasta para abrir o processo.
        <HelpTooltip content={TM_HELP_TOOLTIPS.processos.modosVisualizacao} ariaLabel="Ajuda: modos de visualização" />
      </p>
    </section>
  );
}
