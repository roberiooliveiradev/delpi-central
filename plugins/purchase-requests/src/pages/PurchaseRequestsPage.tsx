import { useCallback, useEffect, useMemo, useState } from "react";

import type { PurchaseRequestListItem } from "../types/purchaseRequests";
import type { PurchaseRequestsAccess } from "../security/purchaseRequestsAccess";
import { usePurchaseRequestDetail } from "../hooks/usePurchaseRequestDetail";
import { usePurchaseRequestRequesters } from "../hooks/usePurchaseRequestRequesters";
import { usePurchaseRequestsList } from "../hooks/usePurchaseRequestsList";
import {
  BASE_PATH,
  buildRequestKey,
  createDefaultUrlState,
  parseRequestKey,
  parseUrlState,
  queryFromUrlState,
  replaceUrlState,
} from "../utils/urlState";
import { resolveListSurfaceState } from "../utils/pageState";
import { PurchaseRequestDetailDrawer } from "../components/PurchaseRequestDetailDrawer";
import { PurchaseRequestsFilters } from "../components/PurchaseRequestsFilters";
import { PurchaseRequestsTable } from "../components/PurchaseRequestsTable";
import { PurchaseRequestsPageHeader } from "../components/PurchaseRequestsPageHeader";
import {
  PurchaseRequestsEmptyState,
  PurchaseRequestsLoadingState,
  PurchaseRequestsSectionCard,
  PurchaseRequestsStateBanner,
} from "../ui/purchaseRequestsUi";
import {
  CompactPaginationControl,
  PAGINATION_CLASS_NAMES,
  PAGINATION_LABELS,
} from "../ui/purchaseRequestsUiContracts";

type PurchaseRequestsPageProps = {
  access: PurchaseRequestsAccess;
  pathname: string;
  search: string;
};

export function PurchaseRequestsPage({ access, pathname, search }: PurchaseRequestsPageProps) {
  const initialBranch = access.defaultBranch;
  const [urlState, setUrlState] = useState(() =>
    parseUrlState(search, initialBranch || "01"),
  );

  useEffect(() => {
    setUrlState(parseUrlState(search, initialBranch || urlState.branch || "01"));
  }, [initialBranch, search]);

  useEffect(() => {
    if (!access.branches.some((branch) => branch.value === urlState.branch)) {
      const fallback = access.defaultBranch;
      if (fallback) {
        setUrlState((current) => ({ ...current, branch: fallback }));
      }
    }
  }, [access.branches, access.defaultBranch, urlState.branch]);

  useEffect(() => {
    replaceUrlState(pathname || BASE_PATH, urlState);
  }, [pathname, urlState]);

  const query = useMemo(() => queryFromUrlState(urlState), [urlState]);
  const enabled = Boolean(access.canView && query.branch);
  const requesterFacetQuery = useMemo(
    () => ({
      branch: query.branch,
      date_from: query.date_from,
      date_to: query.date_to,
      request_number: query.request_number,
      cost_center: query.cost_center,
      product_code: query.product_code,
      supplier_code: query.supplier_code,
      order_number: query.order_number,
    }),
    [
      query.branch,
      query.cost_center,
      query.date_from,
      query.date_to,
      query.order_number,
      query.product_code,
      query.request_number,
      query.supplier_code,
    ],
  );
  const { items: requesterOptions, loading: requestersLoading } = usePurchaseRequestRequesters(
    requesterFacetQuery,
    enabled,
  );
  const { data, loading, error, hasLoaded, reload } = usePurchaseRequestsList(query, enabled);

  const detailTarget = useMemo(() => parseRequestKey(urlState.request), [urlState.request]);
  const detailFilters = useMemo(
    () => ({
      date_from: query.date_from,
      date_to: query.date_to,
      cost_center: query.cost_center,
    }),
    [query.cost_center, query.date_from, query.date_to],
  );
  const {
    data: detail,
    loading: detailLoading,
    error: detailError,
    notFound: detailNotFound,
    reload: reloadDetail,
  } = usePurchaseRequestDetail(detailTarget, detailFilters);

  const surface = resolveListSurfaceState({
    loading,
    error,
    itemCount: data?.items.length ?? 0,
    hasLoaded,
  });

  const patchState = useCallback((patch: Partial<typeof urlState>) => {
    setUrlState((current) => ({ ...current, ...patch }));
  }, []);

  const clearFilters = useCallback(() => {
    const branch = urlState.branch || access.defaultBranch || "01";
    setUrlState(createDefaultUrlState(branch));
  }, [access.defaultBranch, urlState.branch]);

  const openDetail = useCallback(
    (item: PurchaseRequestListItem) => {
      patchState({ request: buildRequestKey(item.branch, item.request_number) });
    },
    [patchState],
  );

  const closeDetail = useCallback(() => {
    patchState({ request: "" });
  }, [patchState]);

  const totalPages = Math.max(1, data?.total_pages ?? 1);

  const branchLabel =
    access.branches.find((item) => item.value === urlState.branch)?.label ??
    `Filial ${urlState.branch}`;

  return (
    <div className="dashboard-purchase-requests dashboard-page">
      <PurchaseRequestsPageHeader
        branchLabel={branchLabel}
        branchCode={urlState.branch}
        dateFrom={urlState.date_from}
        dateTo={urlState.date_to}
        onRefresh={reload}
        refreshing={loading && hasLoaded}
      />

      <PurchaseRequestsFilters
        state={urlState}
        access={access}
        requesterOptions={requesterOptions}
        requestersLoading={requestersLoading}
        onChange={patchState}
        onClear={clearFilters}
      />

      {surface === "loading" ? <PurchaseRequestsLoadingState /> : null}

      {surface === "error" ? (
        <div className="pr-page-error">
          <PurchaseRequestsStateBanner variant="error">{error}</PurchaseRequestsStateBanner>
          <button type="button" className="pr-btn pr-btn--secondary" onClick={() => void reload()}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {surface === "empty" ? (
        <PurchaseRequestsEmptyState>
          <button type="button" className="pr-btn pr-btn--secondary" onClick={clearFilters}>
            Limpar filtros
          </button>
        </PurchaseRequestsEmptyState>
      ) : null}

      {surface === "ready" && data ? (
        <>
          <PurchaseRequestsSectionCard title="Solicitações">
            <PurchaseRequestsTable
              items={data.items}
              loading={loading && hasLoaded}
              onSelect={openDetail}
            />
            <CompactPaginationControl
              classNames={PAGINATION_CLASS_NAMES}
              labels={PAGINATION_LABELS}
              layout="flat"
              page={data.page}
              pageSize={data.page_size}
              total={data.total}
              totalPages={totalPages}
              onPageChange={(page) => patchState({ page })}
              disabled={loading}
            />
          </PurchaseRequestsSectionCard>
        </>
      ) : null}

      <PurchaseRequestDetailDrawer
        open={Boolean(detailTarget)}
        onClose={closeDetail}
        loading={detailLoading}
        error={detailError}
        notFound={detailNotFound}
        detail={detail}
        onRetry={() => void reloadDetail()}
      />
    </div>
  );
}
