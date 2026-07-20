import { useCallback, useMemo, useState } from "react";

import { DeficitByUnit } from "../components/DeficitByUnit";
import { EssPageNav } from "../components/EssPageNav";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { PageHeader } from "../components/PageHeader";
import { SafetyStockDetailModal } from "../components/SafetyStockDetailModal";
import { SafetyStockFilters } from "../components/SafetyStockFilters";
import { SafetyStockSummary } from "../components/SafetyStockSummary";
import { SafetyStockTable } from "../components/SafetyStockTable";
import { SectionError } from "../components/SectionError";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useSafetyStockFilters } from "../hooks/useSafetyStockFilters";
import { useSafetyStockItems } from "../hooks/useSafetyStockItems";
import { useSafetyStockSummary } from "../hooks/useSafetyStockSummary";
import {
  DEFAULT_PAGE_SIZE,
  DEFAULT_QUERY_PARAMS,
  MAX_PAGE_SIZE,
  type SafetyStockFiltersData,
  type SafetyStockItem,
  type SafetyStockQueryParams,
} from "../types/safetyStock";

function resolveEffectiveBranch(
  selectedBranch: string,
  options: SafetyStockFiltersData | null,
): string {
  const authorized = options?.authorized_branches ?? [];
  if (selectedBranch && authorized.includes(selectedBranch)) {
    return selectedBranch;
  }
  if (authorized.length === 1) {
    return authorized[0];
  }
  if (!selectedBranch && options?.branch) {
    return options.branch;
  }
  return selectedBranch;
}

function buildAppliedParams(
  filters: SafetyStockQueryParams,
  debouncedSearch: string,
  branch: string,
): SafetyStockQueryParams | null {
  if (!branch) return null;
  return {
    ...filters,
    branch,
    search: debouncedSearch.trim(),
  };
}

export function SafetyStockPage() {
  const [filters, setFilters] = useState<SafetyStockQueryParams>(DEFAULT_QUERY_PARAMS);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [selectedItem, setSelectedItem] = useState<SafetyStockItem | null>(null);

  const filterOptions = useSafetyStockFilters(filters.branch, filters.includeBlocked);

  const effectiveBranch = useMemo(
    () => resolveEffectiveBranch(filters.branch, filterOptions.data),
    [filters.branch, filterOptions.data],
  );

  const displayFilters = useMemo(
    () => ({ ...filters, branch: effectiveBranch }),
    [filters, effectiveBranch],
  );

  const debouncedSearch = useDebouncedValue(filters.search, 350);

  const appliedParams = useMemo(
    () => buildAppliedParams(filters, debouncedSearch, effectiveBranch),
    [filters, debouncedSearch, effectiveBranch],
  );

  const summary = useSafetyStockSummary(appliedParams);
  const items = useSafetyStockItems(appliedParams, page, pageSize);

  const handleFilterChange = useCallback((patch: Partial<SafetyStockQueryParams>) => {
    setFilters((current) => ({ ...current, ...patch }));
    setPage(1);
  }, []);

  const handleClearFilters = useCallback(() => {
    const branch = effectiveBranch || filterOptions.data?.authorized_branches[0] || "";
    setFilters({
      ...DEFAULT_QUERY_PARAMS,
      branch,
    });
    setPage(1);
  }, [effectiveBranch, filterOptions.data?.authorized_branches]);

  const handleRefresh = useCallback(() => {
    filterOptions.reload();
    summary.reload();
    items.reload();
  }, [filterOptions, items, summary]);

  const handlePageSizeChange = useCallback((nextPageSize: number) => {
    setPageSize(Math.min(nextPageSize, MAX_PAGE_SIZE));
    setPage(1);
  }, []);

  const initialFiltersLoading = filterOptions.loading && !filterOptions.data;
  const showContent =
    Boolean(effectiveBranch) && (filterOptions.data !== null || !filterOptions.error);

  const emptyTableMessage =
    appliedParams?.status === "below_safety_stock"
      ? "Não existem materiais abaixo do estoque de segurança nesta filial."
      : "Nenhuma matéria-prima encontrada para os filtros selecionados.";

  return (
    <div className="dashboard-estoque-seguranca dashboard-page ess-page">
      <div className="ess-app-shell">
        <PageHeader
          branch={effectiveBranch}
          onRefresh={handleRefresh}
          refreshing={
            filterOptions.loading || summary.refreshing || items.refreshing
          }
          nav={<EssPageNav active="monitor" />}
        />

        {initialFiltersLoading ? (
          <LoadingActivityCard
            title="Carregando filtros"
            description="Obtendo filiais autorizadas e opções de consulta."
            progressPercent={0}
          />
        ) : null}

        {filterOptions.error && !filterOptions.data ? (
          <SectionError
            title={filterOptions.error.title}
            message={filterOptions.error.message}
            onRetry={filterOptions.error.retryable ? filterOptions.reload : undefined}
          />
        ) : null}

        {showContent ? (
          <>
            <SafetyStockFilters
              filters={displayFilters}
              options={filterOptions.data}
              loading={filterOptions.loading}
              onChange={handleFilterChange}
              onClear={handleClearFilters}
            />

            {summary.error ? (
              <SectionError
                title={summary.error.title}
                message={summary.error.message}
                onRetry={summary.error.retryable ? summary.reload : undefined}
              />
            ) : (
              <SafetyStockSummary
                summary={summary.data}
                loading={summary.loading}
                refreshing={summary.refreshing}
              />
            )}

            {!summary.error ? (
              <DeficitByUnit rows={summary.data?.deficit_by_unit ?? []} />
            ) : null}

            {items.error ? (
              <SectionError
                title={items.error.title}
                message={items.error.message}
                onRetry={items.error.retryable ? items.reload : undefined}
              />
            ) : (
              <SafetyStockTable
                items={items.data?.items ?? []}
                exportParams={appliedParams}
                loading={items.loading}
                refreshing={items.refreshing}
                page={items.data?.page ?? page}
                pageSize={items.data?.page_size ?? pageSize}
                total={items.data?.total ?? 0}
                emptyMessage={emptyTableMessage}
                onPageChange={setPage}
                onPageSizeChange={handlePageSizeChange}
                onRowClick={setSelectedItem}
              />
            )}

            <SafetyStockDetailModal
              item={selectedItem}
              onClose={() => setSelectedItem(null)}
              onNavigate={setSelectedItem}
            />
          </>
        ) : null}
      </div>
    </div>
  );
}
