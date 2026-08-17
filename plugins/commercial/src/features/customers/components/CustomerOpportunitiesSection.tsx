import { HelpTooltip } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useState } from "react";

import { getCommercialProposals } from "../../../api/analyticsApi";
import {
  CommercialActionButton,
  CommercialDateField,
  CommercialEmptyState,
  CommercialFilterBarShell,
  CommercialLoadingCard,
  CommercialScopeChipBar,
  CommercialSectionCard,
  CommercialTextField,
} from "../../../app/commercialUi";
import { navigatePluginView } from "../../../app/pluginNavigation";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { CM_HELP } from "../../../content/helpTooltips";
import type {
  CommercialProposal,
  CommercialProposalStatusCategory,
} from "../../../types/analytics";
import { CommercialProposalsTable } from "../../analytics/components/CommercialProposalsTable";

type CustomerOpportunitiesSectionProps = {
  basePath: string;
  customerCode: string;
  canViewAnalytics: boolean;
  canViewProposals?: boolean;
};

type StatusFilter = "all" | CommercialProposalStatusCategory;

const TEXT_FILTER_DEBOUNCE_MS = 300;

function useDebouncedValue(value: string, delayMs: number): string {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timeoutId = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(timeoutId);
  }, [delayMs, value]);
  return debounced;
}

/**
 * Lista real de OVs do cliente (mesmo contrato da página global, filtrada por código).
 */
export function CustomerOpportunitiesSection({
  basePath,
  customerCode,
  canViewAnalytics,
  canViewProposals = false,
}: CustomerOpportunitiesSectionProps) {
  const [items, setItems] = useState<CommercialProposal[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [search, setSearch] = useState("");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [productCode, setProductCode] = useState("");
  const [productGroup, setProductGroup] = useState("");
  const debouncedSearch = useDebouncedValue(search, TEXT_FILTER_DEBOUNCE_MS);
  const debouncedProductCode = useDebouncedValue(productCode, TEXT_FILTER_DEBOUNCE_MS);
  const debouncedProductGroup = useDebouncedValue(productGroup, TEXT_FILTER_DEBOUNCE_MS);
  const code = customerCode.trim();
  const detailSearch = code
    ? `?${new URLSearchParams({ search: code }).toString()}`
    : undefined;
  const copy = ANALYTICS_CONTENT.oportunidades;
  const showInitialLoader = loading && items.length === 0;

  useEffect(() => {
    if (!canViewAnalytics || !code) {
      setLoading(false);
      setItems([]);
      setTotal(0);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    const apiStatus =
      statusFilter === "open" || statusFilter === "won" ? statusFilter : undefined;
    const ovSearch = debouncedSearch.trim();
    const product = debouncedProductCode.trim();
    const group = debouncedProductGroup.trim();

    void getCommercialProposals(
      {
        page: 1,
        page_size: 100,
        sort_by: "proposal_date",
        sort_dir: "desc",
        account_customer_code: code,
        status: apiStatus,
        start_date: dateStart.trim() || undefined,
        end_date: dateEnd.trim() || undefined,
        product_code: product || undefined,
        product_group: group || undefined,
        search: ovSearch || undefined,
      },
      controller.signal,
    )
      .then((page) => {
        if (controller.signal.aborted) return;
        const rows = (page.items ?? []).filter(
          (row) => (row.customer_code || "").trim() === code,
        );
        setItems(rows);
        setTotal(typeof page.total === "number" ? page.total : rows.length);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar oportunidades.");
        setItems([]);
        setTotal(0);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    canViewAnalytics,
    code,
    statusFilter,
    dateStart,
    dateEnd,
    debouncedProductCode,
    debouncedProductGroup,
    debouncedSearch,
  ]);

  const statusCounts = useMemo(() => {
    const counts: Record<StatusFilter, number> = {
      all: items.length,
      open: 0,
      won: 0,
      lost: 0,
      other: 0,
    };
    for (const row of items) {
      const category = row.status_category ?? "other";
      counts[category] += 1;
    }
    return counts;
  }, [items]);

  const filteredItems = useMemo(() => {
    return items.filter((row) => {
      if (statusFilter === "lost" || statusFilter === "other") {
        const category = row.status_category ?? "other";
        if (category !== statusFilter) return false;
      }
      return true;
    });
  }, [items, statusFilter]);

  if (!canViewAnalytics) {
    return (
      <CommercialEmptyState
        title={copy.title}
        message="Você não possui permissão para consultar oportunidades."
      />
    );
  }

  if (!code) {
    return (
      <CommercialEmptyState
        title={copy.title}
        message="Cliente sem código para filtrar oportunidades."
      />
    );
  }

  return (
    <CommercialSectionCard
      title={`Oportunidades (${filteredItems.length.toLocaleString("pt-BR")}${
        filteredItems.length !== total
          ? ` de ${total.toLocaleString("pt-BR")}`
          : ""
      })`}
      hint={CM_HELP.customerDetail.opportunities}
      actions={
        <CommercialActionButton
          variant="ghost"
          onClick={() =>
            navigatePluginView("analytics_opportunities", {
              basePath,
              search: `?${new URLSearchParams({ search: code }).toString()}`,
            })
          }
        >
          Ver todas
        </CommercialActionButton>
      }
    >
      <CommercialScopeChipBar
        aria-label={copy.statusFilterAriaLabel}
        label={
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            {copy.statusFilterLabel}
            <HelpTooltip
              content={CM_HELP.customerDetail.opportunitiesStatusFilter}
              ariaLabel="Ajuda: filtro de status"
            />
          </span>
        }
        chips={[
          {
            id: "all",
            label: `${copy.statusAll}${
              statusFilter === "all"
                ? ` (${statusCounts.all.toLocaleString("pt-BR")})`
                : ""
            }`,
            active: statusFilter === "all",
            onSelect: () => setStatusFilter("all"),
          },
          {
            id: "open",
            label: copy.statusOpen,
            active: statusFilter === "open",
            onSelect: () => setStatusFilter("open"),
          },
          {
            id: "won",
            label: copy.statusWon,
            active: statusFilter === "won",
            onSelect: () => setStatusFilter("won"),
          },
          {
            id: "lost",
            label: copy.statusLost,
            active: statusFilter === "lost",
            onSelect: () => setStatusFilter("lost"),
          },
          {
            id: "other",
            label: copy.statusOther,
            active: statusFilter === "other",
            onSelect: () => setStatusFilter("other"),
          },
        ]}
      />
      <CommercialFilterBarShell embedded ariaLabel={copy.accountFiltersAriaLabel}>
        <CommercialDateField
          label={copy.dateStartLabel}
          hint={CM_HELP.customerDetail.opportunitiesDateStart}
          value={dateStart}
          onChange={setDateStart}
        />
        <CommercialDateField
          label={copy.dateEndLabel}
          hint={CM_HELP.customerDetail.opportunitiesDateEnd}
          value={dateEnd}
          onChange={setDateEnd}
        />
        <CommercialTextField
          label={copy.searchLabel}
          hint={CM_HELP.customerDetail.opportunitiesSearch}
          placeholder={copy.searchPlaceholder}
          value={search}
          onChange={setSearch}
        />
        <CommercialTextField
          label={copy.productCodeLabel}
          hint={CM_HELP.customerDetail.opportunitiesProductCode}
          placeholder={copy.productCodePlaceholder}
          value={productCode}
          onChange={setProductCode}
        />
        <CommercialTextField
          label={copy.productGroupLabel}
          hint={CM_HELP.customerDetail.opportunitiesProductGroup}
          placeholder={copy.productGroupPlaceholder}
          value={productGroup}
          onChange={setProductGroup}
        />
      </CommercialFilterBarShell>

      {showInitialLoader ? (
        <CommercialLoadingCard title="Carregando oportunidades…" variant="panel" />
      ) : null}
      {error ? <CommercialEmptyState defaultMessage={error} /> : null}
      {!showInitialLoader && !error ? (
        <div aria-busy={loading || undefined}>
          {items.length === 0 ? (
            <CommercialEmptyState
              defaultTitle="Nenhuma OV neste filtro"
              defaultMessage="Não há oportunidades com este código de cliente no recorte atual."
            />
          ) : null}
          {items.length > 0 && filteredItems.length === 0 ? (
            <CommercialEmptyState defaultMessage={copy.emptyFiltered} />
          ) : null}
          {filteredItems.length > 0 ? (
            <CommercialProposalsTable
              rows={filteredItems}
              basePath={basePath}
              detailSearch={detailSearch}
              hideCustomerColumn
              showOpenProposal={canViewProposals}
            />
          ) : null}
        </div>
      ) : null}
    </CommercialSectionCard>
  );
}
