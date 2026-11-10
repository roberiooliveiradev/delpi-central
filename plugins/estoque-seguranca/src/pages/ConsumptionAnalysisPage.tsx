import { useCallback, useEffect, useMemo, useState } from "react";

import { ConsumptionAnalysisDetailModal } from "../components/ConsumptionAnalysisDetailModal";
import { ConsumptionAnalysisDistribution } from "../components/ConsumptionAnalysisDistribution";
import { ConsumptionAnalysisFilters } from "../components/ConsumptionAnalysisFilters";
import { ConsumptionAnalysisSummary } from "../components/ConsumptionAnalysisSummary";
import { ConsumptionAnalysisTable } from "../components/ConsumptionAnalysisTable";
import { EssPageNav } from "../components/EssPageNav";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { PageHeader } from "../components/PageHeader";
import { ProductQuickSearch } from "../components/ProductQuickSearch";
import { SectionError } from "../components/SectionError";
import { useConsumptionAnalysisItems } from "../hooks/useConsumptionAnalysisItems";
import { useConsumptionAnalysisSummary } from "../hooks/useConsumptionAnalysisSummary";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useSafetyStockFilters } from "../hooks/useSafetyStockFilters";
import {
  DEFAULT_ANALYSIS_QUERY_PARAMS,
  type ConsumptionAnalysisItem,
  type ConsumptionAnalysisQueryParams,
} from "../types/consumptionAnalysis";
import { DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE } from "../types/safetyStock";
import {
  readPreferredSafetyStockBranch,
  resolveAuthorizedSafetyStockBranch,
  savePreferredSafetyStockBranch,
} from "../utils/branchPreference";

function buildAppliedParams(
  filters: ConsumptionAnalysisQueryParams,
  debouncedSearch: string,
  branch: string,
): ConsumptionAnalysisQueryParams | null {
  if (!branch) return null;
  return {
    ...filters,
    branch,
    search: debouncedSearch.trim(),
  };
}

export function ConsumptionAnalysisPage() {
  const [preferredBranch] = useState(readPreferredSafetyStockBranch);
  const [filters, setFilters] = useState<ConsumptionAnalysisQueryParams>(
    DEFAULT_ANALYSIS_QUERY_PARAMS,
  );
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [selectedItem, setSelectedItem] = useState<ConsumptionAnalysisItem | null>(null);

  const filterOptions = useSafetyStockFilters(filters.branch, filters.includeBlocked);
  const effectiveBranch = useMemo(
    () => resolveAuthorizedSafetyStockBranch(filters.branch, filterOptions.data, preferredBranch),
    [filters.branch, filterOptions.data, preferredBranch],
  );
  // Primeiro consultamos as filiais autorizadas; nunca confiamos diretamente no storage.
  useEffect(() => {
    if (!filterOptions.data || !effectiveBranch || filters.branch === effectiveBranch) return;
    setFilters((current) =>
      current.branch === effectiveBranch ? current : { ...current, branch: effectiveBranch },
    );
  }, [effectiveBranch, filterOptions.data, filters.branch]);

  const debouncedSearch = useDebouncedValue(filters.search, 350);
  const appliedParams = useMemo(
    () => buildAppliedParams(filters, debouncedSearch, effectiveBranch),
    [filters, debouncedSearch, effectiveBranch],
  );

  const summary = useConsumptionAnalysisSummary(appliedParams);
  const items = useConsumptionAnalysisItems(appliedParams, page, pageSize);

  const handleFilterChange = useCallback(
    (patch: Partial<ConsumptionAnalysisQueryParams>) => {
      if (patch.branch && filterOptions.data?.authorized_branches.includes(patch.branch)) {
        savePreferredSafetyStockBranch(patch.branch);
      }
      setFilters((current) => ({ ...current, ...patch }));
      setPage(1);
    },
    [filterOptions.data],
  );

  const handleClearFilters = useCallback(() => {
    const branch = effectiveBranch || filterOptions.data?.authorized_branches[0] || "";
    setFilters({
      ...DEFAULT_ANALYSIS_QUERY_PARAMS,
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

  const initialFiltersLoading =
    (filterOptions.loading && !filterOptions.data) ||
    (Boolean(filterOptions.data) && !filters.branch);
  const showContent =
    Boolean(filters.branch && effectiveBranch) && (filterOptions.data !== null || !filterOptions.error);
  const displayFilters = useMemo(
    () => ({ ...filters, branch: effectiveBranch }),
    [filters, effectiveBranch],
  );

  return (
    <div className="dashboard-estoque-seguranca dashboard-page ess-page">
      <div className="ess-app-shell">
        <PageHeader
          branch={effectiveBranch}
          onRefresh={handleRefresh}
          refreshing={summary.refreshing || items.refreshing || filterOptions.loading}
          title="Análise de estoque de segurança"
          subtitle="Qual ESTSEG cobrir o lead time com base no consumo real das baixas dos últimos 12 meses?"
          nav={<EssPageNav active="analysis" />}
        />

        {initialFiltersLoading ? (
          <LoadingActivityCard
            title="Carregando filtros"
            description="Consultando opções autorizadas da filial."
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
            <ProductQuickSearch
              mode="analysis"
              branch={effectiveBranch}
              disabled={filterOptions.loading}
              onSelect={setSelectedItem}
            />

            {summary.error && !summary.data ? (
              <SectionError
                title={summary.error.title}
                message={summary.error.message}
                onRetry={summary.error.retryable ? summary.reload : undefined}
              />
            ) : (
              <>
                <ConsumptionAnalysisSummary
                  summary={summary.data}
                  loading={summary.loading}
                  refreshing={summary.refreshing}
                />
                <ConsumptionAnalysisDistribution
                  summary={summary.data}
                  loading={summary.loading}
                />
              </>
            )}

            <ConsumptionAnalysisFilters
              filters={displayFilters}
              options={filterOptions.data}
              loading={filterOptions.loading}
              onChange={handleFilterChange}
              onClear={handleClearFilters}
            />

            {items.error && !items.data ? (
              <SectionError
                title={items.error.title}
                message={items.error.message}
                onRetry={items.error.retryable ? items.reload : undefined}
              />
            ) : (
              <ConsumptionAnalysisTable
                items={items.data?.items ?? []}
                exportParams={appliedParams}
                loading={items.loading}
                refreshing={items.refreshing}
                page={page}
                pageSize={pageSize}
                total={items.data?.total ?? 0}
                onPageChange={setPage}
                onPageSizeChange={handlePageSizeChange}
                onRowClick={setSelectedItem}
                emptyMessage={
                  appliedParams?.analysisStatus === "below_suggested"
                    ? "Não há itens abaixo do estoque sugerido para os filtros atuais."
                    : undefined
                }
              />
            )}
          </>
        ) : null}

        <ConsumptionAnalysisDetailModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onNavigate={setSelectedItem}
        />
      </div>
    </div>
  );
}
