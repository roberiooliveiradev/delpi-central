import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ArrowDownAZ, ArrowUpAZ, Grid2X2, LayoutGrid, LayoutList, Rows3 } from "lucide-react";

import type { DataTableColumn } from "../../components/DataTable";
import { DataTable } from "../../components/DataTable";
import { FieldLabel, HelpTooltip } from "@delpi/plugin-ui/index";
import { SelectField } from "../../components/ui/SelectField";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { Pagination } from "../../components/Pagination";
import { ProcessoFormProgress } from "../../components/processo/ProcessoFormProgress";
import { useClientPagination } from "../../hooks/useClientPagination";
import type { Processo } from "../../data/api/transformometroApi";
import { buildProcessoPath } from "../../utils/routeParser";
import { handleSpaLinkClick } from "../../utils/spaLink";
import { computeProcessoListCompletion } from "../../utils/processoCompletion";
import { renderTableStatus } from "../../utils/tablePresentation";
import { ProcessoFolderIcon } from "./ProcessoFolderIcon";
import {
  PROCESSO_LIST_SORT_OPTIONS,
  readProcessoListSort,
  sortProcessoListItems,
  writeProcessoListSort,
  type ProcessoListSort,
  type ProcessoListSortField,
} from "./processoListSort";
import {
  fieldVisibilityForProcessoListView,
  pageSizeForProcessoListView,
  PROCESSO_LIST_VIEW_MODES,
  readProcessoListViewMode,
  writeProcessoListViewMode,
  type ProcessoListFieldVisibility,
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
  onNavigate: (path: string) => void;
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

function processoFolderTitle(processo: Processo): string {
  return `${processo.codigo_processo} — ${processo.nome_processo}`;
}

type FolderCardProps = {
  processo: Processo;
  iconSize: "lg" | "md";
  visibility: ProcessoListFieldVisibility;
  href: string;
  onNavigate: (path: string) => void;
};

function ProcessoFolderCard({ processo, iconSize, visibility, href, onNavigate }: FolderCardProps) {
  const minimal = !visibility.showCode && !visibility.showMeta && !visibility.showStatus && !visibility.showProgress;

  return (
    <article className={`tm-processo-folder${minimal ? " tm-processo-folder--minimal" : ""}`} role="listitem">
      <a
        href={href}
        className="tm-processo-folder__open"
        title={processoFolderTitle(processo)}
        onClick={(event) => handleSpaLinkClick(event, href, onNavigate)}
      >
        <ProcessoFolderIcon size={iconSize} />
        {visibility.showCode ? (
          <span className="tm-processo-folder__code">{processo.codigo_processo}</span>
        ) : null}
        <span className="tm-processo-folder__name">{processo.nome_processo}</span>
        {visibility.showMeta ? <span className="tm-processo-folder__meta">{folderMeta(processo)}</span> : null}
        {visibility.showStatus ? (
          <span className="tm-processo-folder__status">{renderTableStatus(processo.status_processo)}</span>
        ) : null}
        {visibility.showProgress ? (
          <ProcessoFormProgress
            compact
            completion={computeProcessoListCompletion(processo)}
            title={`Preenchimento — ${processo.codigo_processo}`}
          />
        ) : null}
      </a>
    </article>
  );
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
  onNavigate,
}: Props) {
  const P = TM_HELP_TOOLTIPS.processos;
  const [viewMode, setViewMode] = useState<ProcessoListViewMode>(() => readProcessoListViewMode());
  const [sort, setSort] = useState<ProcessoListSort>(() => readProcessoListSort());

  useEffect(() => {
    writeProcessoListViewMode(viewMode);
  }, [viewMode]);

  useEffect(() => {
    writeProcessoListSort(sort);
  }, [sort]);

  const sortedItems = useMemo(() => sortProcessoListItems(items, sort), [items, sort]);
  const fieldVisibility = fieldVisibilityForProcessoListView(viewMode);

  const pageSize = pageSizeForProcessoListView(viewMode);
  const { page, setPage, slice, total } = useClientPagination(sortedItems, pageSize);

  function handleSortChange(columnKey: string) {
    const key = columnKey as ProcessoListSortField;
    if (!PROCESSO_LIST_SORT_OPTIONS.some((option) => option.value === key)) return;
    setSort((current) => {
      if (current.key === key) {
        return { key, direction: current.direction === "asc" ? "desc" : "asc" };
      }
      return { key, direction: "asc" };
    });
  }

  function handleSortFieldChange(field: string) {
    const key = field as ProcessoListSortField;
    if (!PROCESSO_LIST_SORT_OPTIONS.some((option) => option.value === key)) return;
    setSort((current) => ({ ...current, key }));
  }

  function toggleSortDirection() {
    setSort((current) => ({
      ...current,
      direction: current.direction === "asc" ? "desc" : "asc",
    }));
  }

  const currentMode = PROCESSO_LIST_VIEW_MODES.find((mode) => mode.id === viewMode)!;
  const sortDirectionLabel = sort.direction === "asc" ? "Menor → maior" : "Maior → menor";

  return (
    <section className={`ds-table-section tm-processo-browser${refreshing ? " tm-processo-browser--refreshing" : ""}`}>
      <div className="ds-table-section__header tm-processo-browser__header">
        <div>
          <h2 className="ds-section-title">{title}</h2>
          {hint ? <p className="ds-hint">{hint}</p> : null}
        </div>
        <div className="tm-processo-browser__toolbar">
          <div className="tm-processo-browser__sort" aria-label="Ordenação da lista">
            <SelectField
              id="tm-proc-sort-field"
              label="Ordenar por"
              hint={P.ordenacaoCampo}
              value={sort.key}
              onChange={handleSortFieldChange}
              options={PROCESSO_LIST_SORT_OPTIONS}
              className="tm-processo-browser__sort-field"
            />
            <div className="tm-processo-browser__sort-direction">
              <FieldLabel className="tm-field__label tm-processo-browser__sort-direction-label" label="Ordem" hint={P.ordenacaoDirecao} />
              <button
                type="button"
                className="tm-processo-browser__sort-direction-btn"
                aria-label={`Ordem: ${sortDirectionLabel}. Clique para alternar.`}
                title={sortDirectionLabel}
                onClick={toggleSortDirection}
              >
                {sort.direction === "asc" ? (
                  <ArrowDownAZ size={16} aria-hidden="true" />
                ) : (
                  <ArrowUpAZ size={16} aria-hidden="true" />
                )}
                <span>{sort.direction === "asc" ? "Menor" : "Maior"}</span>
              </button>
            </div>
          </div>
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
          sortKey={sort.key}
          sortDirection={sort.direction}
          onSortChange={handleSortChange}
        />
      ) : viewMode === "list" ? (
        <ul className="tm-processo-browser__list" role="list">
          {slice.map((processo) => {
            const href = buildProcessoPath(processo.processo_id);
            return (
            <li key={processo.processo_id}>
              <a
                href={href}
                className="tm-processo-browser__list-item"
                title={processoFolderTitle(processo)}
                onClick={(event) => handleSpaLinkClick(event, href, onNavigate)}
              >
                <ProcessoFolderIcon size="sm" />
                <span className="tm-processo-browser__list-main">
                  <span className="tm-processo-browser__list-title">{processo.nome_processo}</span>
                  <span className="tm-processo-browser__list-meta">
                    {fieldVisibility.showCode ? `${processo.codigo_processo} · ` : ""}
                    {folderMeta(processo)}
                  </span>
                </span>
                {fieldVisibility.showStatus ? (
                  <span className="tm-processo-browser__list-status">{renderTableStatus(processo.status_processo)}</span>
                ) : null}
                {fieldVisibility.showProgress ? (
                  <ProcessoFormProgress
                    compact
                    completion={computeProcessoListCompletion(processo)}
                    title={`Preenchimento — ${processo.codigo_processo}`}
                  />
                ) : null}
              </a>
            </li>
            );
          })}
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
            <ProcessoFolderCard
              key={processo.processo_id}
              processo={processo}
              iconSize={viewMode === "icons-lg" ? "lg" : "md"}
              visibility={fieldVisibility}
              href={buildProcessoPath(processo.processo_id)}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      )}

      <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />

      {footer ? <div className="tm-processo-browser__footer">{footer}</div> : null}

      <p className="ds-hint tm-processo-browser__mode-hint">
        Visualização: {currentMode.label}. Clique na pasta para abrir o processo.
        <HelpTooltip content={P.modosVisualizacao} ariaLabel="Ajuda: modos de visualização" />
      </p>
    </section>
  );
}
