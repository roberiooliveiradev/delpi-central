/** Central de solicitações PRC — hero canônico, filtros oficiais,
 * DataTableSection com paginação do servidor e estados honestos.
 * Nenhum dado é inventado: agregados/KPIs só existiriam se a API
 * fornecesse totais por status (ela não fornece → omitidos). */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { HomeApiError } from "../../../api/httpClient";
import { usePrcQueueSync } from "../../../app/EngineeringRealtimeProvider";
import { navigateEngineeringView } from "../../../app/engineeringRoutes";
import {
  EngineeringActionButton,
  EngineeringDataCardsGrid,
  EngineeringEmptyState,
  EngineeringFilterInput,
  EngineeringFiltersRow,
  EngineeringInteractiveDataCard,
  EngineeringKanbanBoard,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
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
            {hasActiveFilters ? (
              <EngineeringActionButton
                variant="ghost"
                onClick={clearFilters}
              >
                {PRC_COPY.clearFilters}
              </EngineeringActionButton>
            ) : null}
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
        <EngineeringFiltersRow ariaLabel="Filtros da fila de solicitações">
          <EngineeringFilterInput
            label={PRC_COPY.searchLabel}
            type="search"
            value={searchDraft}
            onChange={setSearchDraft}
            placeholder={PRC_COPY.searchPlaceholder}
          />
          {/* §41 — Status/Tipo como grupos de seleção exclusiva
           * (SegmentToggle canônico, aria-pressed): o preset
           * `view=pending` aparece como "Pendentes" ativo no próprio
           * grupo, sem aviso desconectado de "Todos os status". */}
          <div className="engineering-filter-box engineering-field delpi-ui-filter-box engineering-filter-box--wide delpi-ui-filter-box--wide">
            <span className="engineering-field__label">
              {PRC_COPY.filterStatusLabel}
            </span>
            <EngineeringSegmentToggle
              ariaLabel={PRC_COPY.filterStatusAriaLabel}
              idPrefix="prc-status-filter"
              size="sm"
              widthMode="content"
              options={PRC_QUEUE_STATUS_OPTIONS}
              value={prcQueueStatusFilterValue(applied)}
              onChange={(value) =>
                commit(prcQueueStateForStatusFilter(applied, value), {
                  replace: false,
                })
              }
            />
          </div>
          <div className="engineering-filter-box engineering-field delpi-ui-filter-box">
            <span className="engineering-field__label">
              {PRC_COPY.filterTypeLabel}
            </span>
            <EngineeringSegmentToggle
              ariaLabel={PRC_COPY.filterTypeAriaLabel}
              idPrefix="prc-type-filter"
              size="sm"
              widthMode="content"
              options={PRC_QUEUE_TYPE_OPTIONS}
              value={applied.type}
              onChange={(value) =>
                commit({ ...applied, type: value, page: 1 }, {
                  replace: false,
                })
              }
            />
          </div>
        </EngineeringFiltersRow>
        {/* PRC-REF-021-REF-01 — bandeiras compactas no hero (sem faixa externa). */}
        {!forbidden ? (
          <PrcFlagsOpsPanel basePath={basePath} compact />
        ) : null}
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
          <div className="engineering-prc__view-toolbar">
            <EngineeringSegmentToggle
              ariaLabel="Modo de apresentação da fila"
              value={layout}
              onChange={setLayout}
              options={[
                { value: "table", label: "Tabela" },
                { value: "cards", label: "Cards" },
                { value: "board", label: "Kanban" },
              ]}
            />
            <EngineeringActionButton
              variant="ghost"
              softDisabled={loading}
              onClick={() => {
                const controller = new AbortController();
                void load(applied, controller.signal);
              }}
            >
              {PRC_COPY.refresh}
            </EngineeringActionButton>
          </div>

          {layout === "table" ? (
            <DataTableSection
              title={PRC_COPY.listTitle}
              columns={columns}
              rows={list.items}
              rowKey={(row) => row.id}
              loading={loading}
              hideSearch
              emptyMessage={PRC_COPY.emptyFiltered}
              columnPreferencesKey="engineering:prc:requests:columns"
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
