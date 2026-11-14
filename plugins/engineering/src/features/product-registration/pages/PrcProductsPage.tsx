/** U1 — Produtos acompanhados: listagem server-side das versões
 * técnicas confirmadas (rota 12b). Não lista o catálogo TOTVS e não
 * oferece cadastro manual — produtos entram por conclusão de PRC. */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FilterX, RefreshCw } from "lucide-react";

import { HomeApiError } from "../../../api/httpClient";
import { navigateEngineeringView } from "../../../app/engineeringRoutes";
import {
  EngineeringActionButton,
  EngineeringEmptyState,
  EngineeringFilterInput,
  EngineeringIconButton,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringScopeChipBar,
  EngineeringStateBanner,
} from "../../../ui/engineeringUi";
import type { DataTableColumn } from "../../lmps/components/dataTableUi";
import { DataTableSection } from "../../lmps/components/DataTableSection";
import {
  fetchPrcProducts,
  type PrcProductSummary,
} from "../api/productRegistrationApi";
import {
  buildPrcQueueUrl,
  EMPTY_PRC_QUEUE_URL,
  navigatePrc,
  navigatePrcHref,
  parsePrcQueueUrl,
  PRC_PATHS,
  useLocationSearch,
} from "../prcNavigate";
import { PRC_COPY, PRC_PRODUCTS_COPY } from "../prcCopy";
import { PrcAreaToggle } from "../components/PrcAreaToggle";

const PAGE_SIZE = 25;
const SEARCH_DEBOUNCE_MS = 400;

/** Coluna UI → sort do contrato backend (direção canônica por
 * chave — o servidor não aceita sortDir; o indicador da tabela
 * espelha a direção efetiva). */
const SORT_BY_COLUMN: Record<
  string,
  { sort: string; dir: "asc" | "desc" }
> = {
  officialCode: { sort: "code", dir: "asc" },
  description: { sort: "description", dir: "asc" },
  lastEvolution: { sort: "lastEvolution", dir: "desc" },
};

const COLUMN_BY_SORT: Record<string, string> = {
  code: "officialCode",
  description: "description",
  lastEvolution: "lastEvolution",
};

function formatEvolution(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR");
  } catch {
    return iso;
  }
}

export function PrcProductsPage({ basePath }: { basePath: string }) {
  const search = useLocationSearch();
  const applied = useMemo(() => parsePrcQueueUrl(search), [search]);

  const [searchDraft, setSearchDraft] = useState(applied.search);
  const [prevApplied, setPrevApplied] = useState(applied);
  if (prevApplied !== applied) {
    setPrevApplied(applied);
    setSearchDraft(applied.search);
  }

  const [list, setList] = useState<{
    items: PrcProductSummary[];
    total: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{
    status: number | null;
    message: string;
  } | null>(null);
  const requestSeq = useRef(0);

  const commit = useCallback(
    (
      state: Parameters<typeof buildPrcQueueUrl>[1],
      options?: { replace?: boolean },
    ) => {
      navigatePrcHref(buildPrcQueueUrl(basePath, state), {
        replace: options?.replace ?? true,
      });
    },
    [basePath],
  );

  const load = useCallback(
    async (
      state: ReturnType<typeof parsePrcQueueUrl>,
      signal: AbortSignal,
    ) => {
      const seq = ++requestSeq.current;
      setLoading(true);
      setError(null);
      try {
        const env = await fetchPrcProducts(
          {
            search: state.search || undefined,
            flagState: state.flagState || undefined,
            sort: state.sortBy || "lastEvolution",
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
          message: err.message || "Falha ao carregar os produtos.",
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

  /* Debounce da busca → URL (replace). */
  useEffect(() => {
    if (searchDraft === applied.search) return undefined;
    const timer = window.setTimeout(() => {
      commit({ ...applied, search: searchDraft.trim(), page: 1 });
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [searchDraft, applied, commit]);

  const hasActiveFilters =
    applied.flagState !== "" ||
    applied.search !== "" ||
    searchDraft !== applied.search;

  const clearFilters = useCallback(() => {
    setSearchDraft("");
    commit(
      { ...applied, search: "", flagState: "", page: 1 },
      { replace: false },
    );
  }, [applied, commit]);

  const openDetail = useCallback(
    (row: PrcProductSummary) => {
      navigatePrc(PRC_PATHS.product(row.recordId), basePath);
    },
    [basePath],
  );

  const submitSearch = useCallback(() => {
    if (searchDraft.trim() === applied.search) return;
    commit({ ...applied, search: searchDraft.trim(), page: 1 });
  }, [applied, commit, searchDraft]);

  const flagChips = useMemo(
    () =>
      [
        { value: "", label: PRC_PRODUCTS_COPY.flagAll },
        { value: "open", label: PRC_PRODUCTS_COPY.flagOpen },
        { value: "none", label: PRC_PRODUCTS_COPY.flagNone },
      ].map((option) => ({
        id: option.value || "all",
        label: option.label,
        active: applied.flagState === option.value,
        onSelect: () =>
          commit(
            {
              ...applied,
              flagState: option.value as "" | "open" | "none",
              page: 1,
            },
            { replace: false },
          ),
      })),
    [applied, commit],
  );

  const columns = useMemo<DataTableColumn<PrcProductSummary>[]>(
    () => [
      {
        key: "officialCode",
        header: PRC_PRODUCTS_COPY.colCode,
        sortable: true,
        render: (row) => row.officialCode,
      },
      {
        key: "description",
        header: PRC_PRODUCTS_COPY.colDescription,
        sortable: true,
        render: (row) =>
          row.description || (
            <span className="engineering-prc__muted">—</span>
          ),
      },
      {
        key: "currentRevisionNumber",
        header: PRC_PRODUCTS_COPY.colVersion,
        sortable: false,
        render: (row) => `V${row.currentRevisionNumber}`,
      },
      {
        key: "openFlagCount",
        header: PRC_PRODUCTS_COPY.colOpenFlags,
        sortable: false,
        render: (row) =>
          row.openFlagCount > 0 ? (
            <span className="engineering-prc__flag-count" aria-label={
              `${row.openFlagCount} bandeira(s) aberta(s)`
            }>
              {row.openFlagCount}
            </span>
          ) : (
            <span className="engineering-prc__muted">—</span>
          ),
      },
      {
        key: "lastEvolution",
        header: PRC_PRODUCTS_COPY.colLastEvolution,
        sortable: true,
        render: (row) => formatEvolution(row.lastEvolutionAt),
      },
    ],
    [],
  );

  const forbidden = error?.status === 403;
  const refresh = useCallback(() => {
    const controller = new AbortController();
    void load(applied, controller.signal);
  }, [applied, load]);

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
        title={PRC_PRODUCTS_COPY.listTitle}
        description={PRC_PRODUCTS_COPY.listDescription}
        actions={
          <>
            {!forbidden && list ? (
              <span
                className="engineering-prc__count-pill"
                aria-live="polite"
                aria-label={`${list.total} ${
                  list.total === 1
                    ? PRC_PRODUCTS_COPY.countSingle
                    : PRC_PRODUCTS_COPY.countPlural
                } no escopo atual`}
              >
                Produtos{" "}
                <strong className="engineering-prc__count-pill-value">
                  {list.total}
                </strong>
              </span>
            ) : null}
            <EngineeringActionButton
              variant="ghost"
              softDisabled={loading}
              onClick={refresh}
            >
              <RefreshCw size={16} aria-hidden /> {PRC_COPY.refresh}
            </EngineeringActionButton>
          </>
        }
      >
        <div className="engineering-prc__queue-controls">
          <PrcAreaToggle
            value="products"
            onChange={(area) => {
              if (area === "requests") {
                commit(EMPTY_PRC_QUEUE_URL, { replace: false });
              }
            }}
          />
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
              placeholder={PRC_PRODUCTS_COPY.searchPlaceholder}
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
              aria-label={PRC_PRODUCTS_COPY.filterFlagsAriaLabel}
              label={PRC_PRODUCTS_COPY.filterFlagsLabel}
              chips={flagChips}
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
            {`Produtos acompanhados indisponíveis — ${error.message}`}
          </EngineeringStateBanner>
          <EngineeringActionButton variant="primary" onClick={refresh}>
            Tentar novamente
          </EngineeringActionButton>
        </>
      ) : null}

      {!forbidden && !error && loading && !list ? (
        <EngineeringLoadingActivityCard
          title="Carregando produtos acompanhados"
          description="Consultando as versões técnicas confirmadas."
        />
      ) : null}

      {!forbidden && !error && !loading && list && list.items.length === 0 ? (
        <EngineeringEmptyState
          message={
            hasActiveFilters
              ? PRC_PRODUCTS_COPY.emptyFiltered
              : PRC_PRODUCTS_COPY.emptyProducts
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
          unframed
          title={PRC_PRODUCTS_COPY.listTitle}
          columns={columns}
          rows={list.items}
          rowKey={(row) => row.recordId}
          loading={loading}
          hideSearch
          emptyMessage={PRC_PRODUCTS_COPY.emptyFiltered}
          serverPagination={{
            page: applied.page,
            pageSize: PAGE_SIZE,
            total: list.total,
            onPageChange: (page) => commit({ ...applied, page }),
          }}
          serverSort={{
            sortKey:
              COLUMN_BY_SORT[applied.sortBy || "lastEvolution"] ||
              null,
            sortDirection: applied.sortDir,
            onSortChange: (columnKey) => {
              const mapped = SORT_BY_COLUMN[columnKey];
              if (!mapped) return;
              commit(
                {
                  ...applied,
                  sortBy: mapped.sort,
                  sortDir: mapped.dir,
                  page: 1,
                },
                { replace: false },
              );
            },
          }}
          onRowClick={openDetail}
        />
      ) : null}
    </main>
  );
}
