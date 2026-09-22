import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  ChevronLeft,
  Grid2X2,
  LayoutGrid,
  LayoutList,
  Rows3,
} from "lucide-react";

import type { DataTableColumn } from "../../components/DataTable";
import { DataTable } from "../../components/DataTable";
import { SegmentToggle } from "../../components/SegmentToggle";
import {
  dataTableSectionBemClasses,
  ensureDelpiUiClass,
  FieldLabel,
  HelpTooltip,
} from "@delpi/plugin-ui/index";
import { SelectField } from "../../components/ui/SelectField";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { Pagination } from "../../components/Pagination";
import { ProcessFormProgress } from "../../components/process/ProcessFormProgress";
import { useClientPagination } from "../../hooks/useClientPagination";
import type { Processo } from "../../data/api/transformometroApi";
import { buildProcessoPath } from "../../utils/routeParser";
import { handleSpaLinkClick } from "../../utils/spaLink";
import { computeProcessoListCompletion } from "../../utils/processoCompletion";
import { renderTableStatus } from "../../utils/tablePresentation";
import { ProcessFolderIcon } from "./ProcessFolderIcon";
import {
  groupProcessesByDepartment,
  sortDepartamentoFolders,
  type DepartamentoFolder,
} from "./groupProcessesByDepartment";
import {
  PROCESSO_LIST_BROWSE_MODES,
  readProcessoListBrowseMode,
  writeProcessoListBrowseMode,
  type ProcessoListBrowseMode,
} from "./processListBrowseMode";
import {
  PROCESSO_LIST_SORT_OPTIONS,
  readProcessoListSort,
  sortProcessoListItems,
  writeProcessoListSort,
  type ProcessoListSort,
  type ProcessoListSortField,
} from "./processListSort";
import {
  fieldVisibilityForProcessoListView,
  pageSizeForProcessoListView,
  PROCESSO_LIST_VIEW_MODES,
  readProcessoListViewMode,
  writeProcessoListViewMode,
  type ProcessoListFieldVisibility,
  type ProcessoListViewMode,
} from "./processListViewMode";
import { ProcessListPresentationControls } from "./ProcessListPresentationControls";

const SECTION_CN = dataTableSectionBemClasses("ds");

type Props = {
  /** Se omitido, não renderiza h2 (ex.: página já tem PageHeader). */
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
  /** Controlled browse mode (Processos / Departamentos). */
  browseMode?: ProcessoListBrowseMode;
  onBrowseModeChange?: (mode: ProcessoListBrowseMode) => void;
  /** Quando true, o toggle Processos/Departamentos fica no Hero da página. */
  hideBrowseToggle?: boolean;
  /** Quando true, oculta a contagem da toolbar (ex.: highlight do Hero é o owner). */
  hideRecordCount?: boolean;
  /** Controlled sort (Hero owns the control). */
  sort?: ProcessoListSort;
  onSortChange?: (sort: ProcessoListSort) => void;
  /** Controlled view mode (Hero owns the control). */
  viewMode?: ProcessoListViewMode;
  onViewModeChange?: (mode: ProcessoListViewMode) => void;
  /** When true, sort/view toolbar is rendered by the page Hero. */
  hideListToolbar?: boolean;
};


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

function departamentoMeta(folder: DepartamentoFolder): string {
  const n = folder.processCount;
  return `${n} processo${n === 1 ? "" : "s"}`;
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
        <ProcessFolderIcon size={iconSize} />
        {visibility.showCode ? (
          <span className="tm-processo-folder__code">{processo.codigo_processo}</span>
        ) : null}
        <span className="tm-processo-folder__name">{processo.nome_processo}</span>
        {visibility.showMeta ? <span className="tm-processo-folder__meta">{folderMeta(processo)}</span> : null}
        {visibility.showStatus ? (
          <span className="tm-processo-folder__status">{renderTableStatus(processo.status_processo)}</span>
        ) : null}
        {visibility.showProgress ? (
          <ProcessFormProgress
            compact
            completion={computeProcessoListCompletion(processo)}
            title={`Preenchimento — ${processo.codigo_processo}`}
          />
        ) : null}
      </a>
    </article>
  );
}

type DepartamentoFolderCardProps = {
  folder: DepartamentoFolder;
  iconSize: "lg" | "md";
  visibility: ProcessoListFieldVisibility;
  onOpen: (folder: DepartamentoFolder) => void;
};

function DepartamentoFolderCard({ folder, iconSize, visibility, onOpen }: DepartamentoFolderCardProps) {
  const minimal = !visibility.showCode && !visibility.showMeta;

  return (
    <article className={`tm-processo-folder${minimal ? " tm-processo-folder--minimal" : ""}`} role="listitem">
      <button
        type="button"
        className="tm-processo-folder__open"
        title={`${folder.label} — ${departamentoMeta(folder)}`}
        onClick={() => onOpen(folder)}
      >
        <ProcessFolderIcon size={iconSize} />
        {visibility.showCode && folder.codigoSetor ? (
          <span className="tm-processo-folder__code">{folder.codigoSetor}</span>
        ) : null}
        <span className="tm-processo-folder__name">{folder.label}</span>
        {visibility.showMeta ? (
          <span className="tm-processo-folder__meta">{departamentoMeta(folder)}</span>
        ) : null}
      </button>
    </article>
  );
}

export function ProcessFolderBrowser({
  title,
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
  browseMode: browseModeProp,
  onBrowseModeChange,
  hideBrowseToggle = false,
  hideRecordCount = false,
  sort: sortProp,
  onSortChange,
  viewMode: viewModeProp,
  onViewModeChange,
  hideListToolbar = false,
}: Props) {
  const P = TM_HELP_TOOLTIPS.processos;
  const [browseModeState, setBrowseModeState] = useState<ProcessoListBrowseMode>(() =>
    readProcessoListBrowseMode(),
  );
  const browseMode = browseModeProp ?? browseModeState;
  const setBrowseMode = (mode: ProcessoListBrowseMode) => {
    onBrowseModeChange?.(mode);
    if (browseModeProp === undefined) setBrowseModeState(mode);
  };
  const [selectedDepartamentoKey, setSelectedDepartamentoKey] = useState<string | null>(null);
  const [viewModeState, setViewModeState] = useState<ProcessoListViewMode>(() => readProcessoListViewMode());
  const [sortState, setSortState] = useState<ProcessoListSort>(() => readProcessoListSort());
  const viewMode = viewModeProp ?? viewModeState;
  const sort = sortProp ?? sortState;

  function setViewMode(mode: ProcessoListViewMode) {
    onViewModeChange?.(mode);
    if (viewModeProp === undefined) setViewModeState(mode);
  }

  function setSort(next: ProcessoListSort | ((current: ProcessoListSort) => ProcessoListSort)) {
    const current = sortProp ?? sortState;
    const resolved = typeof next === "function" ? next(current) : next;
    onSortChange?.(resolved);
    if (sortProp === undefined) setSortState(resolved);
  }

  useEffect(() => {
    if (browseModeProp === undefined) writeProcessoListBrowseMode(browseModeState);
  }, [browseModeProp, browseModeState]);

  useEffect(() => {
    if (viewModeProp === undefined) writeProcessoListViewMode(viewModeState);
  }, [viewModeProp, viewModeState]);

  useEffect(() => {
    if (sortProp === undefined) writeProcessoListSort(sortState);
  }, [sortProp, sortState]);

  useEffect(() => {
    if (browseMode !== "departamento") {
      setSelectedDepartamentoKey(null);
    }
  }, [browseMode]);

  const departamentoFolders = useMemo(() => {
    const grouped = groupProcessesByDepartment(items);
    return sortDepartamentoFolders(grouped, sort.direction);
  }, [items, sort.direction]);

  const selectedDepartamento = useMemo(
    () => departamentoFolders.find((folder) => folder.key === selectedDepartamentoKey) ?? null,
    [departamentoFolders, selectedDepartamentoKey],
  );

  useEffect(() => {
    if (selectedDepartamentoKey && !selectedDepartamento) {
      setSelectedDepartamentoKey(null);
    }
  }, [selectedDepartamento, selectedDepartamentoKey]);

  const showingDepartamentoRoot = browseMode === "departamento" && !selectedDepartamento;
  const processoItems = useMemo(() => {
    if (browseMode === "processo") return items;
    return selectedDepartamento?.processes ?? [];
  }, [browseMode, items, selectedDepartamento]);

  const sortedProcessos = useMemo(
    () => sortProcessoListItems(processoItems, sort),
    [processoItems, sort],
  );

  const fieldVisibility = fieldVisibilityForProcessoListView(viewMode);
  const pageSize = pageSizeForProcessoListView(viewMode);

  const departamentoPagination = useClientPagination(departamentoFolders, pageSize);
  const processoPagination = useClientPagination(sortedProcessos, pageSize);
  const { page, setPage, total } = showingDepartamentoRoot
    ? departamentoPagination
    : processoPagination;

  const departamentoSlice = showingDepartamentoRoot ? departamentoPagination.slice : [];
  const processoSlice = showingDepartamentoRoot ? [] : processoPagination.slice;

  const departamentoDetailColumns = useMemo<DataTableColumn<DepartamentoFolder>[]>(
    () => [
      {
        key: "label",
        header: "Departamento",
        sortable: false,
        render: (row) => row.label,
      },
      {
        key: "codigo",
        header: "Código",
        sortable: false,
        render: (row) => row.codigoSetor || "—",
      },
      {
        key: "count",
        header: "Processos",
        sortable: false,
        render: (row) => String(row.processCount),
      },
    ],
    [],
  );

  function handleBrowseModeChange(mode: ProcessoListBrowseMode) {
    setBrowseMode(mode);
    setSelectedDepartamentoKey(null);
    setPage(1);
  }

  function handleOpenDepartamento(folder: DepartamentoFolder) {
    setSelectedDepartamentoKey(folder.key);
    setPage(1);
  }

  function handleBackToDepartamentos() {
    setSelectedDepartamentoKey(null);
    setPage(1);
  }

  function handleSortChange(columnKey: string) {
    const key = columnKey as ProcessoListSortField;
    if (!PROCESSO_LIST_SORT_OPTIONS.some((option) => option.value === key)) return;
    setSort((current) => {
      if (current.key === key) {
        return { key, direction: current.direction === "asc" ? "desc" : "asc" };
      }
      return { key, direction: key === "atualizado" ? "desc" : "asc" };
    });
  }



  const currentMode = PROCESSO_LIST_VIEW_MODES.find((mode) => mode.id === viewMode)!;
  const showSectionHeading = Boolean(title || hint);

  const countLabel = showingDepartamentoRoot
    ? `${total} departamento${total === 1 ? "" : "s"}`
    : browseMode === "departamento" && selectedDepartamento
      ? `${total} processo${total === 1 ? "" : "s"} em ${selectedDepartamento.label}`
      : `${total} registro${total === 1 ? "" : "s"}`;

  const modeHint = showingDepartamentoRoot
    ? "Visão por departamento. Clique na pasta para ver os processos daquele departamento (um processo pode aparecer em mais de um)."
    : browseMode === "departamento" && selectedDepartamento
      ? `Processos do departamento «${selectedDepartamento.label}». Clique na pasta para abrir o processo.`
      : `Visualização: ${currentMode.label}. Clique na pasta para abrir o processo.`;

  return (
    <section
      className={ensureDelpiUiClass(
        `ds-table-section tm-processo-browser${refreshing ? " tm-processo-browser--refreshing" : ""}`,
        "delpi-ui-table-section",
      )}
    >
      {showSectionHeading ? (
        <div className={`${SECTION_CN.header} tm-processo-browser__header`}>
          <div>
            {title ? <h2 className={SECTION_CN.title}>{title}</h2> : null}
            {hint ? <p className="ds-hint">{hint}</p> : null}
          </div>
        </div>
      ) : null}

      {browseMode === "departamento" && selectedDepartamento ? (
        <div className="tm-processo-browser__browse-row tm-processo-browser__browse-row--drill">
          <nav className="tm-processo-browser__breadcrumb" aria-label="Navegação por departamento">
            <button
              type="button"
              className="tm-processo-browser__breadcrumb-back"
              onClick={handleBackToDepartamentos}
            >
              <ChevronLeft size={16} aria-hidden="true" />
              Departamentos
            </button>
            <span className="tm-processo-browser__breadcrumb-sep" aria-hidden="true">
              /
            </span>
            <span className="tm-processo-browser__breadcrumb-current">{selectedDepartamento.label}</span>
          </nav>
        </div>
      ) : !hideBrowseToggle ? (
        <div className="tm-processo-browser__browse-row">
          <div className="tm-processo-browser__browse-label">
            <FieldLabel
              className="tm-field__label"
              label="Visualizar por"
              hint={P.visaoOrganizacao}
            />
            <p className="ds-hint tm-processo-browser__browse-hint">
              {browseMode === "departamento"
                ? "Agrupamento por departamento do escopo (preferência salva neste navegador)."
                : "Listagem plana de macroprocessos (preferência salva neste navegador)."}
            </p>
          </div>
          <div className="tm-processo-browser__browse-toggle">
            <SegmentToggle
              ariaLabel="Visualizar listagem por processos ou departamentos"
              idPrefix="tm-proc-browse"
              prefix="ds"
              size="md"
              options={PROCESSO_LIST_BROWSE_MODES.map((mode) => ({
                value: mode.id,
                label: mode.label,
              }))}
              value={browseMode}
              onChange={handleBrowseModeChange}
            />
          </div>
        </div>
      ) : null}

      {filters ? <div className="tm-processo-browser__filters">{filters}</div> : null}

      {!hideListToolbar ? (
        <div
          className={`${SECTION_CN.toolbar} tm-processo-browser__toolbar`}
          aria-label="Configuração da listagem"
        >
          <ProcessListPresentationControls
            sort={sort}
            onSortFieldChange={(field) =>
              setSort((current) => ({
                key: field,
                direction:
                  field === "atualizado" && current.key !== "atualizado"
                    ? "desc"
                    : current.direction,
              }))
            }
            onToggleSortDirection={() =>
              setSort((current) => ({
                ...current,
                direction: current.direction === "asc" ? "desc" : "asc",
              }))
            }
            departmentRoot={showingDepartamentoRoot}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
          />
          {hideRecordCount ? null : (
            <span className={`${SECTION_CN.meta} tm-processo-browser__count`}>{countLabel}</span>
          )}
        </div>
      ) : null}

      {loading ? (
        <p className="ds-hint">Carregando processos…</p>
      ) : total === 0 ? (
        <p className="ds-hint">
          {showingDepartamentoRoot ? "Nenhum departamento encontrado nos processos listados." : emptyMessage}
        </p>
      ) : showingDepartamentoRoot ? (
        viewMode === "details" ? (
          <DataTable
            columns={departamentoDetailColumns}
            rows={departamentoSlice}
            rowKey={(row) => row.key}
            onRowClick={handleOpenDepartamento}
          />
        ) : viewMode === "list" ? (
          <ul className="tm-processo-browser__list" role="list">
            {departamentoSlice.map((folder) => (
              <li key={folder.key}>
                <button
                  type="button"
                  className="tm-processo-browser__list-item"
                  title={`${folder.label} — ${departamentoMeta(folder)}`}
                  onClick={() => handleOpenDepartamento(folder)}
                >
                  <ProcessFolderIcon size="sm" />
                  <span className="tm-processo-browser__list-main">
                    <span className="tm-processo-browser__list-title">{folder.label}</span>
                    <span className="tm-processo-browser__list-meta">
                      {fieldVisibility.showCode && folder.codigoSetor ? `${folder.codigoSetor} · ` : ""}
                      {departamentoMeta(folder)}
                    </span>
                  </span>
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
            {departamentoSlice.map((folder) => (
              <DepartamentoFolderCard
                key={folder.key}
                folder={folder}
                iconSize={viewMode === "icons-lg" ? "lg" : "md"}
                visibility={fieldVisibility}
                onOpen={handleOpenDepartamento}
              />
            ))}
          </div>
        )
      ) : viewMode === "details" ? (
        <DataTable
          columns={detailColumns}
          rows={processoSlice}
          rowKey={(row) => row.processo_id}
          onRowClick={onOpen}
          sortKey={sort.key}
          sortDirection={sort.direction}
          onSortChange={handleSortChange}
        />
      ) : viewMode === "list" ? (
        <ul className="tm-processo-browser__list" role="list">
          {processoSlice.map((processo) => {
            const href = buildProcessoPath(processo.processo_id);
            return (
              <li key={processo.processo_id}>
                <a
                  href={href}
                  className="tm-processo-browser__list-item"
                  title={processoFolderTitle(processo)}
                  onClick={(event) => handleSpaLinkClick(event, href, onNavigate)}
                >
                  <ProcessFolderIcon size="sm" />
                  <span className="tm-processo-browser__list-main">
                    <span className="tm-processo-browser__list-title">{processo.nome_processo}</span>
                    <span className="tm-processo-browser__list-meta">
                      {fieldVisibility.showCode ? `${processo.codigo_processo} · ` : ""}
                      {folderMeta(processo)}
                    </span>
                  </span>
                  {fieldVisibility.showStatus ? (
                    <span className="tm-processo-browser__list-status">
                      {renderTableStatus(processo.status_processo)}
                    </span>
                  ) : null}
                  {fieldVisibility.showProgress ? (
                    <ProcessFormProgress
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
          {processoSlice.map((processo) => (
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
        {modeHint}
        <HelpTooltip content={P.visaoOrganizacao} ariaLabel="Ajuda: visualizar por" />
      </p>
    </section>
  );
}
