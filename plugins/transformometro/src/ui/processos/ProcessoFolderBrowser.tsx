import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  ArrowDownAZ,
  ArrowUpAZ,
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
import { ProcessoFormProgress } from "../../components/processo/ProcessoFormProgress";
import { useClientPagination } from "../../hooks/useClientPagination";
import type { Processo } from "../../data/api/transformometroApi";
import { buildProcessoPath } from "../../utils/routeParser";
import { handleSpaLinkClick } from "../../utils/spaLink";
import { computeProcessoListCompletion } from "../../utils/processoCompletion";
import { renderTableStatus } from "../../utils/tablePresentation";
import { ProcessoFolderIcon } from "./ProcessoFolderIcon";
import {
  groupProcessosByDepartamento,
  sortDepartamentoFolders,
  type DepartamentoFolder,
} from "./groupProcessosByDepartamento";
import {
  PROCESSO_LIST_BROWSE_MODES,
  readProcessoListBrowseMode,
  writeProcessoListBrowseMode,
  type ProcessoListBrowseMode,
} from "./processoListBrowseMode";
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
        <ProcessoFolderIcon size={iconSize} />
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

export function ProcessoFolderBrowser({
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
}: Props) {
  const P = TM_HELP_TOOLTIPS.processos;
  const [browseMode, setBrowseMode] = useState<ProcessoListBrowseMode>(() => readProcessoListBrowseMode());
  const [selectedDepartamentoKey, setSelectedDepartamentoKey] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ProcessoListViewMode>(() => readProcessoListViewMode());
  const [sort, setSort] = useState<ProcessoListSort>(() => readProcessoListSort());

  useEffect(() => {
    writeProcessoListBrowseMode(browseMode);
  }, [browseMode]);

  useEffect(() => {
    writeProcessoListViewMode(viewMode);
  }, [viewMode]);

  useEffect(() => {
    writeProcessoListSort(sort);
  }, [sort]);

  useEffect(() => {
    if (browseMode !== "departamento") {
      setSelectedDepartamentoKey(null);
    }
  }, [browseMode]);

  const departamentoFolders = useMemo(() => {
    const grouped = groupProcessosByDepartamento(items);
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

  const listForPagination = showingDepartamentoRoot ? departamentoFolders : sortedProcessos;
  const { page, setPage, slice, total } = useClientPagination(listForPagination, pageSize);

  const departamentoSlice = showingDepartamentoRoot
    ? (slice as DepartamentoFolder[])
    : [];
  const processoSlice = showingDepartamentoRoot ? [] : (slice as Processo[]);

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

  function handleSortFieldChange(field: string) {
    const key = field as ProcessoListSortField;
    if (!PROCESSO_LIST_SORT_OPTIONS.some((option) => option.value === key)) return;
    setSort((current) => ({
      key,
      direction: key === "atualizado" && current.key !== "atualizado" ? "desc" : current.direction,
    }));
  }

  function toggleSortDirection() {
    setSort((current) => ({
      ...current,
      direction: current.direction === "asc" ? "desc" : "asc",
    }));
  }

  const currentMode = PROCESSO_LIST_VIEW_MODES.find((mode) => mode.id === viewMode)!;
  const sortDirectionLabel = sort.direction === "asc" ? "Menor → maior" : "Maior → menor";
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

      <div className="tm-processo-browser__browse-row">
        <div className="tm-processo-browser__browse-label">
          <FieldLabel
            className="tm-field__label"
            label="Visualizar por"
            hint={P.visaoOrganizacao}
          />
          {browseMode === "departamento" && selectedDepartamento ? (
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
          ) : (
            <p className="ds-hint tm-processo-browser__browse-hint">
              {browseMode === "departamento"
                ? "Pastas por departamento do escopo (preferência salva neste navegador)."
                : "Listagem plana de macroprocessos (preferência salva neste navegador)."}
            </p>
          )}
        </div>
        <div className="tm-processo-browser__browse-toggle">
          <SegmentToggle
            ariaLabel="Visualizar listagem por processos ou departamentos"
            idPrefix="tm-proc-browse"
            options={PROCESSO_LIST_BROWSE_MODES.map((mode) => ({
              value: mode.id,
              label: mode.label,
            }))}
            value={browseMode}
            onChange={handleBrowseModeChange}
          />
        </div>
      </div>

      {filters ? <div className="tm-processo-browser__filters">{filters}</div> : null}

      <div
        className={`${SECTION_CN.toolbar} tm-processo-browser__toolbar`}
        aria-label="Configuração da listagem"
      >
        <div className="tm-processo-browser__sort" aria-label="Ordenação da lista">
          {!showingDepartamentoRoot ? (
            <SelectField
              id="tm-proc-sort-field"
              label="Ordenar por"
              hint={P.ordenacaoCampo}
              value={sort.key}
              onChange={handleSortFieldChange}
              options={PROCESSO_LIST_SORT_OPTIONS}
              className="tm-processo-browser__sort-field"
            />
          ) : (
            <span className="tm-processo-browser__sort-field-static">
              <FieldLabel className="tm-field__label" label="Ordenar por" hint={P.ordenacaoCampo} />
              <span className="ds-hint">Nome do departamento</span>
            </span>
          )}
          <div className="tm-processo-browser__sort-direction">
            <FieldLabel
              className="tm-field__label tm-processo-browser__sort-direction-label"
              label="Ordem"
              hint={P.ordenacaoDirecao}
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
          <span className={`${SECTION_CN.meta} tm-processo-browser__count`}>{countLabel}</span>
        </div>
      </div>

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
                  <ProcessoFolderIcon size="sm" />
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
                  <ProcessoFolderIcon size="sm" />
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
