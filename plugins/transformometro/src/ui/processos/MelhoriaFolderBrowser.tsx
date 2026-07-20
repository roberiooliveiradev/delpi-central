import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ArrowDownAZ, ArrowUpAZ, Grid2X2, LayoutGrid, LayoutList, Rows3 } from "lucide-react";

import type { DataTableColumn } from "../../components/DataTable";
import { DataTable } from "../../components/DataTable";
import {
  dataTableSectionBemClasses,
  ensureDelpiUiClass,
  FieldLabel,
  HelpTooltip,
} from "@delpi/plugin-ui/index";
import { SelectField } from "../../components/ui/SelectField";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { Pagination } from "../../components/Pagination";
import { useClientPagination } from "../../hooks/useClientPagination";
import type { ProcessoInstancia } from "../../data/api/transformometroApi";
import { renderTableStatus } from "../../utils/tablePresentation";
import { ProcessoFolderIcon } from "./ProcessoFolderIcon";
import {
  fieldVisibilityForMelhoriaListView,
  MELHORIA_LIST_VIEW_MODES,
  pageSizeForMelhoriaListView,
  readMelhoriaListViewMode,
  writeMelhoriaListViewMode,
  type MelhoriaListFieldVisibility,
  type MelhoriaListViewMode,
} from "./melhoriaListViewMode";
import {
  MELHORIA_LIST_SORT_OPTIONS,
  melhoriaFolderMeta,
  melhoriaFolderTitle,
  readMelhoriaListSort,
  sortMelhoriaListItems,
  writeMelhoriaListSort,
  type MelhoriaListSort,
  type MelhoriaListSortField,
} from "./melhoriaListSort";
import { formatInstanciaUnidadeDisplay } from "./processoEscopo";

const SECTION_CN = dataTableSectionBemClasses("ds");

type Props = {
  items: ProcessoInstancia[];
  activeFilialCount: number;
  selectedInstanciaId?: string | null;
  loading?: boolean;
  emptyMessage?: string;
  headerActions?: ReactNode;
  detailColumns: DataTableColumn<ProcessoInstancia>[];
  onOpen: (instancia: ProcessoInstancia) => void;
};

function viewModeIcon(mode: MelhoriaListViewMode) {
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

type FolderCardProps = {
  instancia: ProcessoInstancia;
  activeFilialCount: number;
  iconSize: "lg" | "md";
  visibility: MelhoriaListFieldVisibility;
  selected: boolean;
  onOpen: (instancia: ProcessoInstancia) => void;
};

function MelhoriaFolderCard({
  instancia,
  activeFilialCount,
  iconSize,
  visibility,
  selected,
  onOpen,
}: FolderCardProps) {
  const title = melhoriaFolderTitle(instancia, activeFilialCount);
  const minimal =
    !visibility.showCode && !visibility.showMeta && !visibility.showStatus && !visibility.showProgress;

  return (
    <article
      className={`tm-processo-folder${minimal ? " tm-processo-folder--minimal" : ""}${
        selected ? " tm-processo-folder--selected" : ""
      }`}
      role="listitem"
    >
      <button
        type="button"
        className="tm-processo-folder__open"
        title={title}
        onClick={() => onOpen(instancia)}
      >
        <ProcessoFolderIcon size={iconSize} />
        {visibility.showCode ? (
          <span className="tm-processo-folder__code">
            {formatInstanciaUnidadeDisplay(instancia, activeFilialCount)}
          </span>
        ) : null}
        <span className="tm-processo-folder__name">{title}</span>
        {visibility.showMeta ? (
          <span className="tm-processo-folder__meta">
            {melhoriaFolderMeta(instancia, activeFilialCount)}
          </span>
        ) : null}
        {visibility.showStatus ? (
          <span className="tm-processo-folder__status">
            {renderTableStatus(instancia.status_instancia ?? "ativo")}
          </span>
        ) : null}
      </button>
    </article>
  );
}

export function MelhoriaFolderBrowser({
  items,
  activeFilialCount,
  selectedInstanciaId = null,
  loading = false,
  emptyMessage = "Nenhuma melhoria cadastrada.",
  headerActions,
  detailColumns,
  onOpen,
}: Props) {
  const I = TM_HELP_TOOLTIPS.instancias;
  const [viewMode, setViewMode] = useState<MelhoriaListViewMode>(() => readMelhoriaListViewMode());
  const [sort, setSort] = useState<MelhoriaListSort>(() => readMelhoriaListSort());

  useEffect(() => {
    writeMelhoriaListViewMode(viewMode);
  }, [viewMode]);

  useEffect(() => {
    writeMelhoriaListSort(sort);
  }, [sort]);

  const sortedItems = useMemo(
    () => sortMelhoriaListItems(items, sort, activeFilialCount),
    [items, sort, activeFilialCount]
  );
  const fieldVisibility = fieldVisibilityForMelhoriaListView(viewMode);
  const pageSize = pageSizeForMelhoriaListView(viewMode);
  const { page, setPage, slice, total } = useClientPagination(sortedItems, pageSize);

  function handleSortChange(columnKey: string) {
    const key = columnKey as MelhoriaListSortField;
    if (!MELHORIA_LIST_SORT_OPTIONS.some((option) => option.value === key)) return;
    setSort((current) => {
      if (current.key === key) {
        return { key, direction: current.direction === "asc" ? "desc" : "asc" };
      }
      return { key, direction: "asc" };
    });
  }

  function handleSortFieldChange(field: string) {
    const key = field as MelhoriaListSortField;
    if (!MELHORIA_LIST_SORT_OPTIONS.some((option) => option.value === key)) return;
    setSort((current) => ({ key, direction: current.direction }));
  }

  function toggleSortDirection() {
    setSort((current) => ({
      ...current,
      direction: current.direction === "asc" ? "desc" : "asc",
    }));
  }

  const currentMode = MELHORIA_LIST_VIEW_MODES.find((mode) => mode.id === viewMode)!;
  const sortDirectionLabel = sort.direction === "asc" ? "Menor → maior" : "Maior → menor";

  return (
    <section
      className={ensureDelpiUiClass(
        "ds-table-section tm-processo-browser tm-melhoria-browser",
        "delpi-ui-table-section"
      )}
    >
      <div className={`${SECTION_CN.header} tm-processo-browser__header`}>
        <div>
          <h2 className={SECTION_CN.title}>
            <span className="ds-field-label">
              Melhorias
              <HelpTooltip content={I.escopo} ariaLabel="Ajuda: Melhorias" />
            </span>
          </h2>
          <p className="ds-hint">
            Cada melhoria aplica o processo a unidades e departamentos — podem se repetir livremente.
            Clique na pasta para abrir escopo, baseline, cenários e medições.
          </p>
        </div>
        {headerActions ? <div className={SECTION_CN.actions}>{headerActions}</div> : null}
      </div>

      <div
        className={`${SECTION_CN.toolbar} tm-processo-browser__toolbar`}
        aria-label="Configuração da listagem de melhorias"
      >
        <div className="tm-processo-browser__sort" aria-label="Ordenação da lista">
          <SelectField
            id="tm-melhoria-sort-field"
            label="Ordenar por"
            hint={I.ordenacaoCampo}
            value={sort.key}
            onChange={handleSortFieldChange}
            options={MELHORIA_LIST_SORT_OPTIONS}
            className="tm-processo-browser__sort-field"
          />
          <div className="tm-processo-browser__sort-direction">
            <FieldLabel
              className="tm-field__label tm-processo-browser__sort-direction-label"
              label="Ordem"
              hint={I.ordenacaoDirecao}
            />
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
        <div className={`${SECTION_CN.toolbarExtra} tm-processo-browser__toolbar-extra`}>
          <div className="tm-processo-browser__view-modes" role="group" aria-label="Modo de visualização">
            {MELHORIA_LIST_VIEW_MODES.map((mode) => {
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
          <span className={`${SECTION_CN.meta} tm-processo-browser__count`}>
            {total} registro{total === 1 ? "" : "s"}
          </span>
        </div>
      </div>

      {loading ? (
        <p className="ds-hint">Carregando melhorias…</p>
      ) : slice.length === 0 ? (
        <p className="ds-hint">{emptyMessage}</p>
      ) : viewMode === "details" ? (
        <DataTable
          columns={detailColumns}
          rows={slice}
          rowKey={(row) => row.instancia_id}
          onRowClick={onOpen}
          sortKey={sort.key}
          sortDirection={sort.direction}
          onSortChange={handleSortChange}
        />
      ) : viewMode === "list" ? (
        <ul className="tm-processo-browser__list" role="list">
          {slice.map((instancia) => {
            const title = melhoriaFolderTitle(instancia, activeFilialCount);
            const selected = selectedInstanciaId === instancia.instancia_id;
            return (
              <li key={instancia.instancia_id}>
                <button
                  type="button"
                  className={`tm-processo-browser__list-item${
                    selected ? " tm-processo-browser__list-item--selected" : ""
                  }`}
                  title={title}
                  onClick={() => onOpen(instancia)}
                >
                  <ProcessoFolderIcon size="sm" />
                  <span className="tm-processo-browser__list-main">
                    <span className="tm-processo-browser__list-title">{title}</span>
                    <span className="tm-processo-browser__list-meta">
                      {fieldVisibility.showCode
                        ? `${formatInstanciaUnidadeDisplay(instancia, activeFilialCount)} · `
                        : ""}
                      {melhoriaFolderMeta(instancia, activeFilialCount)}
                    </span>
                  </span>
                  {fieldVisibility.showStatus ? (
                    <span className="tm-processo-browser__list-status">
                      {renderTableStatus(instancia.status_instancia ?? "ativo")}
                    </span>
                  ) : null}
                </button>
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
          {slice.map((instancia) => (
            <MelhoriaFolderCard
              key={instancia.instancia_id}
              instancia={instancia}
              activeFilialCount={activeFilialCount}
              iconSize={viewMode === "icons-lg" ? "lg" : "md"}
              visibility={fieldVisibility}
              selected={selectedInstanciaId === instancia.instancia_id}
              onOpen={onOpen}
            />
          ))}
        </div>
      )}

      <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />

      <p className="ds-hint tm-processo-browser__mode-hint">
        Visualização: {currentMode.label}. Clique na pasta para abrir a melhoria.
        <HelpTooltip content={I.modosVisualizacao} ariaLabel="Ajuda: modos de visualização" />
      </p>
    </section>
  );
}
