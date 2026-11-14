/** Central de solicitações PRC — hero canônico, filtros oficiais,
 * DataTableSection com paginação do servidor e estados honestos.
 * Nenhum dado é inventado: agregados/KPIs só existiriam se a API
 * fornecesse totais por status (ela não fornece → omitidos). */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FilterX, RefreshCw } from "lucide-react";

import {
  DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS,
  TableColumnVisibilityMenu,
  useTableColumnVisibility,
} from "@delpi/plugin-ui/index";
import { HomeApiError } from "../../../api/httpClient";
import { usePrcQueueSync } from "../../../app/EngineeringRealtimeProvider";
import { navigateEngineeringView } from "../../../app/engineeringRoutes";
import {
  EngineeringActionButton,
  EngineeringDataCardsGrid,
  EngineeringEmptyState,
  EngineeringFilterInput,
  EngineeringIconButton,
  EngineeringInteractiveDataCard,
  EngineeringKanbanBoard,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringScopeChipBar,
  EngineeringSegmentToggle,
  EngineeringStateBanner,
  usePersistedViewLayout,
} from "../../../ui/engineeringUi";
import type { DataTableColumn } from "../../lmps/components/dataTableUi";
import { DataTableSection } from "../../lmps/components/DataTableSection";
import {
  fetchPrcQueue,
  type PrcRequestSummary,
} from "../api/productRegistrationApi";
import {
  buildPrcQueueUrl,
  navigatePrc,
  navigatePrcHref,
  parsePrcQueueUrl,
  prcQueueStateForStatusFilter,
  prcQueueStatusFilterValue,
  useLocationSearch,
  PRC_PATHS,
  type PrcQueueUrlState,
} from "../prcNavigate";
import {
  PRC_COPY,
  PRC_QUEUE_STATUS_OPTIONS,
  PRC_QUEUE_TYPE_OPTIONS,
  PRC_STATUS_LABELS,
  PRC_TYPE_LABELS,
  prcShortId,
} from "../prcCopy";
import { PrcStatusBadge } from "../components/PrcStatusBadge";
import { PrcPersonCell } from "../components/PrcPersonCell";
import { PrcFlagsOpsPanel } from "../components/PrcFlagsOpsPanel";

const PAGE_SIZE = 25;
const SEARCH_DEBOUNCE_MS = 400;
const COLUMN_PREFERENCES_KEY = "engineering:prc:requests:columns";

export function PrcQueuePage({ basePath }: { basePath: string }) {
  const search = useLocationSearch();
  const applied = useMemo(() => parsePrcQueueUrl(search), [search]);

  /** Draft da busca — digitado aqui, commitado na URL após debounce. */
  const [searchDraft, setSearchDraft] = useState(applied.search);
  const [prevApplied, setPrevApplied] = useState(applied);
  if (prevApplied !== applied) {
    setPrevApplied(applied);
    setSearchDraft(applied.search);
  }

  const [list, setList] = useState<{
    items: PrcRequestSummary[];
    total: number;
    statusCounts: Record<string, number>;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{
    status: number | null;
    message: string;
  } | null>(null);
  const requestSeq = useRef(0);

  const commit = useCallback(
    (state: PrcQueueUrlState, options?: { replace?: boolean }) => {
      navigatePrcHref(buildPrcQueueUrl(basePath, state), {
        replace: options?.replace ?? true,
      });
    },
    [basePath],
  );

  const load = useCallback(
    async (state: PrcQueueUrlState, signal: AbortSignal) => {
      const seq = ++requestSeq.current;
      setLoading(true);
      setError(null);
      try {
        const env = await fetchPrcQueue(
          {
            status: state.status,
            view: state.view,
            type: state.type,
            search: state.search,
            page: state.page,
            pageSize: PAGE_SIZE,
            sortBy: state.sortBy || undefined,
            sortDir: state.sortBy ? state.sortDir : undefined,
          },
          signal,
        );
        if (seq !== requestSeq.current || signal.aborted) return;
        setList({
          items: env.data.items,
          total: env.data.total,
          statusCounts: env.data.statusCounts || {},
        });
      } catch (e) {
        if (seq !== requestSeq.current || signal.aborted) return;
        const err = e as HomeApiError;
        setError({
          status: err.status ?? null,
          message: err.message || "Falha ao carregar a fila.",
        });
        setList(null);
      } finally {
        if (seq === requestSeq.current && !signal.aborted) {
          setLoading(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    void load(applied, controller.signal);
    return () => controller.abort();
  }, [applied, load]);

  /* ENG-REALTIME-01 — evento de mudança invalida e rebusca a fila com
   * os filtros atuais (debounce no provider; WS nunca carrega dado). */
  const appliedRef = useRef(applied);
  appliedRef.current = applied;
  usePrcQueueSync(
    useCallback(() => {
      const controller = new AbortController();
      void load(appliedRef.current, controller.signal);
    }, [load]),
  );

  /* Debounce da busca → URL (replace, sem poluir histórico). */
  useEffect(() => {
    if (searchDraft === applied.search) return undefined;
    const timer = window.setTimeout(() => {
      commit({ ...applied, search: searchDraft.trim(), page: 1 });
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [searchDraft, applied, commit]);

  const hasActiveFilters =
    applied.view !== "" ||
    applied.status !== "" ||
    applied.type !== "" ||
    applied.search !== "" ||
    searchDraft !== applied.search;

  const clearFilters = useCallback(() => {
    setSearchDraft("");
    commit(
      { view: "", status: "", type: "", search: "", page: 1, sortBy: "", sortDir: "desc" },
      { replace: false },
    );
  }, [commit]);

  const openDetail = useCallback(
    (row: PrcRequestSummary) => {
      navigatePrc(PRC_PATHS.detail(row.id), basePath);
    },
    [basePath],
  );

  const { layout, setLayout } = usePersistedViewLayout({
    storageKey: "engineering:prc:requests:layout",
    defaultMode: "table",
  });

  const columns = useMemo<DataTableColumn<PrcRequestSummary>[]>(
    () => [
      {
        key: "id",
        header: "Nº",
        sortable: true,
        render: (row) => (
          <span title={`ID completo: ${row.id}`}>{prcShortId(row.id)}</span>
        ),
      },
      {
        key: "type",
        header: "Tipo",
        sortable: true,
        render: (row) => PRC_TYPE_LABELS[row.requestType] || row.requestType,
      },
      {
        key: "requester",
        header: "Solicitante",
        sortable: true,
        render: (row) => (
          <PrcPersonCell
            subject={row.requester.subject}
            displayName={row.requester.displayName}
          />
        ),
      },
      {
        key: "officialCode",
        header: "Código oficial",
        sortable: true,
        render: (row) =>
          row.officialCode ? (
            row.officialCode
          ) : (
            <span className="engineering-prc__muted">
              {PRC_COPY.awaitingCode}
            </span>
          ),
      },
      {
        key: "createdAt",
        header: "Abertura",
        sortable: true,
        render: (row) => new Date(row.createdAt).toLocaleString("pt-BR"),
      },
      {
        key: "status",
        header: "Status",
        sortable: true,
        render: (row) => <PrcStatusBadge status={row.status} />,
      },
      {
        key: "assignedTo",
        header: "Responsável",
        sortable: true,
        render: (row) => (
          <PrcPersonCell
            subject={row.assignedTo}
            displayName={row.assignedToDisplayName}
            emptyLabel={PRC_COPY.unassigned}
          />
        ),
      },
    ],
    [openDetail],
  );

  /** §43 — preferências de coluna elevadas ao hero (mesma storage key):
   * o menu Colunas fica na barra primária como em Meus Chamados de TI,
   * sem duplicar o estado interno da DataTableSection. */
  const columnCatalog = useMemo(
    () => columns.map((column) => ({ key: column.key, label: column.header })),
    [columns],
  );
  const {
    visibility,
    orderedColumns,
    reorderColumns,
    setColumnVisible,
    reset: resetColumns,
    filterColumns,
  } = useTableColumnVisibility({
    storageKey: COLUMN_PREFERENCES_KEY,
    columns: columnCatalog,
  });
  const visibleColumns = useMemo(
    () => filterColumns(columns),
    [filterColumns, columns],
  );

  const refresh = useCallback(() => {
    const controller = new AbortController();
    void load(applied, controller.signal);
  }, [applied, load]);

  const statusFilter = prcQueueStatusFilterValue(applied);
  const statusChips = useMemo(
    () =>
      PRC_QUEUE_STATUS_OPTIONS.map((option) => ({
        id: option.value || "all",
        label: option.label,
        active: statusFilter === option.value,
        onSelect: () =>
          commit(prcQueueStateForStatusFilter(applied, option.value), {
            replace: false,
          }),
      })),
    [applied, commit, statusFilter],
  );
  const typeChips = useMemo(
    () =>
      PRC_QUEUE_TYPE_OPTIONS.map((option) => ({
        id: option.value || "all",
        label: option.label,
        active: applied.type === option.value,
        onSelect: () =>
          commit({ ...applied, type: option.value, page: 1 }, {
            replace: false,
          }),
      })),
    [applied, commit],
  );

  const submitSearch = useCallback(() => {
    if (searchDraft.trim() === applied.search) return;
    commit({ ...applied, search: searchDraft.trim(), page: 1 });
  }, [applied, commit, searchDraft]);

  const forbidden = error?.status === 403;
  const notFound = error?.status === 404;

  return (
    <main className="engineering-prc">
      <EngineeringPagePath
        back={{
          label: PRC_COPY.breadcrumbHome,
          href: basePath,
          onNavigate: (event) => {
            event.preventDefault();
            navigateEngineeringView("home", { basePath });
          },
        }}
        items={[]}
        current={PRC_COPY.breadcrumbRoot}
      />

      {/* §43 — hero em padrão Meus Chamados de TI: linha 1 título+ações,
       * linha 2 busca dominante + controles compactos (limpar, colunas,
       * atualizar), linha 3 chips rápidos de status + tipo + modo de
       * visualização. Semântica dos filtros e preset inalterada (§41). */}
      <EngineeringPageHero
        eyebrow="Portal Engenharia"
        title={PRC_COPY.listTitle}
        description={PRC_COPY.listDescription}
        actions={
          <>
            {/* §46 — contador do universo filtrado como pill compacta
             * (COUNT real pré-paginação; fail-closed sem lista). */}
            {!forbidden && list ? (
              <span
                className="engineering-prc__count-pill"
                aria-live="polite"
                aria-label={`${list.total} ${
                  list.total === 1 ? "solicitação" : "solicitações"
                } no escopo atual`}
              >
                Solicitações{" "}
                <strong className="engineering-prc__count-pill-value">
                  {list.total}
                </strong>
              </span>
            ) : null}
            {/* PRC-REF-021-REF-01 — entrada compacta das bandeiras na
             * linha de ações do hero (painel expande como popover). */}
            {!forbidden ? (
              <PrcFlagsOpsPanel basePath={basePath} compact />
            ) : null}
            <EngineeringActionButton
              variant="ghost"
              softDisabled={loading}
              onClick={refresh}
            >
              <RefreshCw size={16} aria-hidden /> {PRC_COPY.refresh}
            </EngineeringActionButton>
            <EngineeringActionButton
              variant="primary"
              title="Abrir uma nova solicitação de cadastro ou alteração"
              onClick={() => navigatePrc(PRC_PATHS.create, basePath)}
            >
              {PRC_COPY.newRequest}
            </EngineeringActionButton>
          </>
        }
      >
        <div className="engineering-prc__queue-controls">
          <form
            className="engineering-prc__queue-primary"
            aria-label="Busca e ações da lista"
            onSubmit={(event) => {
              event.preventDefault();
              submitSearch();
            }}
          >
            <EngineeringFilterInput
              label={PRC_COPY.searchLabel}
              type="search"
              value={searchDraft}
              onChange={setSearchDraft}
              placeholder={PRC_COPY.searchPlaceholder}
            />
            <div className="engineering-prc__queue-primary-actions">
              {hasActiveFilters ? (
                <EngineeringIconButton
                  aria-label={PRC_COPY.clearFilters}
                  onClick={clearFilters}
                >
                  <FilterX size={16} aria-hidden />
                </EngineeringIconButton>
              ) : null}
            </div>
          </form>
          <div className="engineering-prc__queue-secondary">
            <EngineeringScopeChipBar
              aria-label={PRC_COPY.filterStatusAriaLabel}
              chips={statusChips}
            />
            <EngineeringScopeChipBar
              aria-label={PRC_COPY.filterTypeAriaLabel}
              label={PRC_COPY.filterTypeLabel}
              chips={typeChips}
            />
          </div>
          {/* §46 — linha inferior do hero: controles de apresentação da
           * grade acoplados ao hero (Colunas só faz sentido em Tabela). */}
          <div className="engineering-prc__queue-bottom">
            {layout === "table" ? (
              <TableColumnVisibilityMenu
                columns={orderedColumns}
                visibility={visibility}
                onToggleColumn={setColumnVisible}
                onReorderColumns={reorderColumns}
                onReset={resetColumns}
                labels={DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS}
              />
            ) : null}
            <EngineeringSegmentToggle
              ariaLabel="Modo de apresentação da fila"
              idPrefix="prc-layout"
              size="sm"
              widthMode="content"
              value={layout}
              onChange={setLayout}
              options={[
                { value: "table", label: "Tabela" },
                { value: "cards", label: "Cards" },
                { value: "board", label: "Kanban" },
              ]}
            />
          </div>
        </div>
      </EngineeringPageHero>

      {forbidden ? (
        <>
          <EngineeringStateBanner variant="error">
            {PRC_COPY.forbidden}
          </EngineeringStateBanner>
          <EngineeringActionButton
            variant="primary"
            onClick={() => navigateEngineeringView("home", { basePath })}
          >
            Voltar ao início
          </EngineeringActionButton>
        </>
      ) : null}

      {!forbidden && error ? (
        <>
          <EngineeringStateBanner variant="error">
            {notFound
              ? "Fila de solicitações não encontrada."
              : `Fila de solicitações indisponível — ${error.message}`}
          </EngineeringStateBanner>
          <EngineeringActionButton
            variant="primary"
            onClick={() => {
              const controller = new AbortController();
              void load(applied, controller.signal);
            }}
          >
            Tentar novamente
          </EngineeringActionButton>
        </>
      ) : null}

      {!forbidden && !error && loading && !list ? (
        <EngineeringLoadingActivityCard
          title="Carregando solicitações"
          description="Consultando a Engineering API com seus filtros."
        />
      ) : null}

      {!forbidden && !error && !loading && list && list.items.length === 0 ? (
        <EngineeringEmptyState
          message={
            hasActiveFilters ? PRC_COPY.emptyFiltered : PRC_COPY.emptyQueue
          }
        >
          {hasActiveFilters ? (
            <EngineeringActionButton variant="ghost" onClick={clearFilters}>
              {PRC_COPY.clearFilters}
            </EngineeringActionButton>
          ) : null}
        </EngineeringEmptyState>
      ) : null}

      {!forbidden && !error && list && list.items.length > 0 ? (
        <div className="engineering-prc__queue-view">
          {layout === "table" ? (
            <DataTableSection
              unframed
              title={PRC_COPY.listTitle}
              columns={visibleColumns}
              rows={list.items}
              rowKey={(row) => row.id}
              loading={loading}
              hideSearch
              emptyMessage={PRC_COPY.emptyFiltered}
              serverPagination={{
                page: applied.page,
                pageSize: PAGE_SIZE,
                total: list.total,
                onPageChange: (page) => commit({ ...applied, page }),
              }}
              serverSort={{
                sortKey: applied.sortBy || null,
                sortDirection: applied.sortDir,
                onSortChange: (columnKey) =>
                  commit({
                    ...applied,
                    sortBy: columnKey,
                    sortDir:
                      applied.sortBy === columnKey &&
                      applied.sortDir === "desc"
                        ? "asc"
                        : "desc",
                    page: 1,
                  }),
              }}
              onRowClick={openDetail}
            />
          ) : null}

          {layout === "cards" ? (
            <>
              <EngineeringDataCardsGrid ariaLabel="Solicitações em cards">
                {list.items.map((row) => (
                  <EngineeringInteractiveDataCard
                    key={row.id}
                    interactive
                    onActivate={() => openDetail(row)}
                    ariaLabel={`Solicitação ${prcShortId(row.id)}`}
                    fields={[
                      {
                        label: "Tipo",
                        value:
                          PRC_TYPE_LABELS[row.requestType] || row.requestType,
                      },
                      { label: "Status", value: <PrcStatusBadge status={row.status} /> },
                      {
                        label: "Código oficial",
                        value: row.officialCode || PRC_COPY.awaitingCode,
                      },
                      {
                        label: "Solicitante",
                        value: (
                          <PrcPersonCell
                            subject={row.requester.subject}
                            displayName={row.requester.displayName}
                          />
                        ),
                      },
                      {
                        label: "Responsável",
                        value: (
                          <PrcPersonCell
                            subject={row.assignedTo}
                            displayName={row.assignedToDisplayName}
                            emptyLabel={PRC_COPY.unassigned}
                          />
                        ),
                      },
                      {
                        label: "Abertura",
                        value: new Date(row.createdAt).toLocaleString("pt-BR"),
                      },
                    ]}
                  >
                    <strong>{prcShortId(row.id)}</strong>
                  </EngineeringInteractiveDataCard>
                ))}
              </EngineeringDataCardsGrid>
              <p className="engineering-prc__muted">
                Página {applied.page} · {list.total} solicitação(ões) no
                escopo.
              </p>
            </>
          ) : null}

          {layout === "board" ? (
            <>
              <EngineeringKanbanBoard
                ariaLabel="Kanban das solicitações por status"
                columns={Object.entries(PRC_STATUS_LABELS).map(
                  ([status, label]) => ({
                    id: status,
                    title: label,
                    count: list.statusCounts[status] ?? 0,
                    empty: <span className="engineering-prc__muted">—</span>,
                    children: list.items
                      .filter((r) => r.status === status)
                      .map((row) => (
                        <EngineeringInteractiveDataCard
                          key={row.id}
                          interactive
                          onActivate={() => openDetail(row)}
                          ariaLabel={`Solicitação ${prcShortId(row.id)}`}
                          fields={[
                            {
                              label: "Tipo",
                              value:
                                PRC_TYPE_LABELS[row.requestType] ||
                                row.requestType,
                            },
                            {
                              label: "Código",
                              value: row.officialCode || PRC_COPY.awaitingCode,
                            },
                            {
                              label: "Solicitante",
                              value: (
                                <PrcPersonCell
                                  subject={row.requester.subject}
                                  displayName={row.requester.displayName}
                                />
                              ),
                            },
                          ]}
                        >
                          <strong>{prcShortId(row.id)}</strong>
                        </EngineeringInteractiveDataCard>
                      )),
                  }),
                )}
              />
              <p className="engineering-prc__muted">
                Contagens por status calculadas pela Engineering API sobre o
                escopo filtrado; os cards exibidos são os itens carregados
                desta página.
              </p>
            </>
          ) : null}
        </div>
      ) : null}
    </main>
  );
}
