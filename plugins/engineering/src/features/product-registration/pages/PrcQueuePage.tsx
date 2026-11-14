/** Central de solicitações PRC — hero canônico, filtros oficiais,
 * DataTableSection com paginação do servidor e estados honestos.
 * §47 — Tabela, Cards e Kanban compartilham catálogo de campos e
 * PrcRequestCard; menu Colunas controla os três modos. */

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
  prcShortId,
} from "../prcCopy";
import {
  PRC_QUEUE_COLUMN_CATALOG,
  PRC_QUEUE_FIELD_LABELS,
  formatPrcKanbanColumnCountMeta,
  formatPrcQueueCreatedAt,
  prcQueueOfficialCodeText,
  prcQueueTypeText,
} from "../prcQueueFieldCatalog";
import { PrcStatusBadge } from "../components/PrcStatusBadge";
import { PrcPersonCell } from "../components/PrcPersonCell";
import { PrcFlagsOpsPanel } from "../components/PrcFlagsOpsPanel";
import {
  PrcRequestCard,
  buildPrcCardColumns,
} from "../components/PrcRequestCard";

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

  /** Catálogo único — mesmas chaves/rótulos/renders para os 3 modos. */
  const columns = useMemo<DataTableColumn<PrcRequestSummary>[]>(
    () => [
      {
        key: "id",
        header: PRC_QUEUE_FIELD_LABELS.id,
        sortable: true,
        render: (row) => (
          <span title={`ID completo: ${row.id}`}>{prcShortId(row.id)}</span>
        ),
      },
      {
        key: "type",
        header: PRC_QUEUE_FIELD_LABELS.type,
        sortable: true,
        render: (row) => prcQueueTypeText(row),
      },
      {
        key: "requester",
        header: PRC_QUEUE_FIELD_LABELS.requester,
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
        header: PRC_QUEUE_FIELD_LABELS.officialCode,
        sortable: true,
        render: (row) =>
          row.officialCode ? (
            row.officialCode
          ) : (
            <span className="engineering-prc__muted">
              {prcQueueOfficialCodeText(row)}
            </span>
          ),
      },
      {
        key: "createdAt",
        header: PRC_QUEUE_FIELD_LABELS.createdAt,
        sortable: true,
        render: (row) => formatPrcQueueCreatedAt(row.createdAt),
      },
      {
        key: "status",
        header: PRC_QUEUE_FIELD_LABELS.status,
        sortable: true,
        render: (row) => <PrcStatusBadge status={row.status} />,
      },
      {
        key: "assignedTo",
        header: PRC_QUEUE_FIELD_LABELS.assignedTo,
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
    [],
  );

  /** Preferências compartilhadas — menu Colunas nos 3 modos. */
  const {
    visibility,
    orderedColumns,
    reorderColumns,
    setColumnVisible,
    reset: resetColumns,
    filterColumns,
  } = useTableColumnVisibility({
    storageKey: COLUMN_PREFERENCES_KEY,
    columns: PRC_QUEUE_COLUMN_CATALOG,
  });
  const visibleColumns = useMemo(
    () => filterColumns(columns),
    [filterColumns, columns],
  );

  const cardColumns = useMemo(
    () => buildPrcCardColumns(columns, visibleColumns),
    [columns, visibleColumns],
  );
  const kanbanCardColumns = useMemo(
    () =>
      buildPrcCardColumns(columns, visibleColumns, { omitKeys: ["status"] }),
    [columns, visibleColumns],
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

      <EngineeringPageHero
        eyebrow="Portal Engenharia"
        title={PRC_COPY.listTitle}
        description={PRC_COPY.listDescription}
        actions={
          <>
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
          {/* §47 — Colunas + modos: menu controla Tabela, Cards e Kanban. */}
          <div className="engineering-prc__queue-bottom">
            <TableColumnVisibilityMenu
              columns={orderedColumns}
              visibility={visibility}
              onToggleColumn={setColumnVisible}
              onReorderColumns={reorderColumns}
              onReset={resetColumns}
              labels={DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS}
            />
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
              <EngineeringDataCardsGrid
                ariaLabel="Solicitações em cards"
                className="engineering-prc__request-cards-grid"
              >
                {list.items.map((row) => (
                  <PrcRequestCard
                    key={row.id}
                    row={row}
                    columns={cardColumns}
                    onOpen={openDetail}
                  />
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
                  ([status, label]) => {
                    const pageItems = list.items.filter(
                      (r) => r.status === status,
                    );
                    const totalInScope = list.statusCounts[status] ?? 0;
                    return {
                      id: status,
                      title: label,
                      count: formatPrcKanbanColumnCountMeta({
                        status,
                        totalInScope,
                        displayedOnPage: pageItems.length,
                      }),
                      empty: (
                        <span className="engineering-prc__muted">—</span>
                      ),
                      children: pageItems.map((row) => (
                        <PrcRequestCard
                          key={row.id}
                          row={row}
                          columns={kanbanCardColumns}
                          onOpen={openDetail}
                        />
                      )),
                    };
                  },
                )}
              />
              <p className="engineering-prc__muted">
                Contagens por status calculadas pela Engineering API sobre o
                escopo filtrado; os cards exibidos são os itens carregados
                desta página (paginação server-side preservada).
              </p>
            </>
          ) : null}
        </div>
      ) : null}
    </main>
  );
}
