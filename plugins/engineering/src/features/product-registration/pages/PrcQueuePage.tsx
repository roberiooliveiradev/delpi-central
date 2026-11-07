/** Central de solicitações PRC — hero canônico, filtros oficiais,
 * DataTableSection com paginação do servidor e estados honestos.
 * Nenhum dado é inventado: agregados/KPIs só existiriam se a API
 * fornecesse totais por status (ela não fornece → omitidos). */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { HomeApiError } from "../../../api/httpClient";
import { navigateEngineeringView } from "../../../app/engineeringRoutes";
import {
  EngineeringActionButton,
  EngineeringEmptyState,
  EngineeringFilterInput,
  EngineeringFilterSelect,
  EngineeringFiltersRow,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringStateBanner,
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
  useLocationSearch,
  PRC_PATHS,
  type PrcQueueUrlState,
} from "../prcNavigate";
import {
  PRC_COPY,
  PRC_STATUS_LABELS,
  PRC_TYPE_LABELS,
  prcPersonLabel,
  prcRequesterLabel,
  prcShortId,
} from "../prcCopy";
import { PrcStatusBadge } from "../components/PrcStatusBadge";

const PAGE_SIZE = 25;
const SEARCH_DEBOUNCE_MS = 400;

const STATUS_OPTIONS = [
  { value: "", label: "Todos os status" },
  ...Object.entries(PRC_STATUS_LABELS).map(([value, label]) => ({
    value,
    label,
  })),
];

const TYPE_OPTIONS = [
  { value: "", label: "Todos os tipos" },
  ...Object.entries(PRC_TYPE_LABELS).map(([value, label]) => ({
    value,
    label,
  })),
];

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
            type: state.type,
            search: state.search,
            page: state.page,
            pageSize: PAGE_SIZE,
          },
          signal,
        );
        if (seq !== requestSeq.current || signal.aborted) return;
        setList({ items: env.data.items, total: env.data.total });
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

  /* Debounce da busca → URL (replace, sem poluir histórico). */
  useEffect(() => {
    if (searchDraft === applied.search) return undefined;
    const timer = window.setTimeout(() => {
      commit({ ...applied, search: searchDraft.trim(), page: 1 });
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [searchDraft, applied, commit]);

  const hasActiveFilters =
    applied.status !== "" ||
    applied.type !== "" ||
    applied.search !== "" ||
    searchDraft !== applied.search;

  const clearFilters = useCallback(() => {
    setSearchDraft("");
    commit({ status: "", type: "", search: "", page: 1 });
  }, [commit]);

  const openDetail = useCallback(
    (row: PrcRequestSummary) => {
      navigatePrc(PRC_PATHS.detail(row.id), basePath);
    },
    [basePath],
  );

  const columns = useMemo<DataTableColumn<PrcRequestSummary>[]>(
    () => [
      {
        key: "id",
        header: "Nº",
        render: (row) => (
          <span title={`ID completo: ${row.id}`}>{prcShortId(row.id)}</span>
        ),
      },
      {
        key: "type",
        header: "Tipo",
        render: (row) => PRC_TYPE_LABELS[row.requestType] || row.requestType,
      },
      {
        key: "requester",
        header: "Solicitante",
        render: (row) => prcRequesterLabel(row.requester),
      },
      {
        key: "officialCode",
        header: "Código oficial",
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
        render: (row) => new Date(row.createdAt).toLocaleString("pt-BR"),
      },
      {
        key: "status",
        header: "Status",
        render: (row) => <PrcStatusBadge status={row.status} />,
      },
      {
        key: "assignedTo",
        header: "Responsável",
        render: (row) => prcPersonLabel(row.assignedTo),
      },
      {
        key: "open",
        header: "",
        interactive: true,
        render: (row) => (
          <EngineeringActionButton
            variant="link"
            title={`${PRC_COPY.openRequest} ${prcShortId(row.id)}`}
            onClick={() => openDetail(row)}
          >
            Abrir
          </EngineeringActionButton>
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
            label="Buscar"
            type="search"
            value={searchDraft}
            onChange={setSearchDraft}
            placeholder="Nº, código oficial ou descrição"
          />
          <EngineeringFilterSelect
            label="Status"
            value={applied.status}
            onChange={(value) =>
              commit({ ...applied, status: value, page: 1 })
            }
            options={STATUS_OPTIONS}
          />
          <EngineeringFilterSelect
            label="Tipo"
            value={applied.type}
            onChange={(value) => commit({ ...applied, type: value, page: 1 })}
            options={TYPE_OPTIONS}
          />
        </EngineeringFiltersRow>
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
        <DataTableSection
          title={PRC_COPY.listTitle}
          columns={columns}
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
          onRowClick={openDetail}
          toolbarActions={
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
          }
        />
      ) : null}
    </main>
  );
}
