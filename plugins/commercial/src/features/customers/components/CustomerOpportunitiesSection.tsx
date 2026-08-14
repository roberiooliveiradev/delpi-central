import { HelpTooltip } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useState } from "react";

import { getCommercialProposals } from "../../../api/analyticsApi";
import {
  CommercialActionButton,
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

function proposalMatchesSearch(row: CommercialProposal, query: string): boolean {
  if (!query) return true;
  const haystack = [
    row.proposal_number,
    row.revision,
    row.status_label,
    row.status_code,
    row.stage,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes(query);
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
  const code = customerCode.trim();
  const detailSearch = code
    ? `?${new URLSearchParams({ search: code }).toString()}`
    : undefined;
  const copy = ANALYTICS_CONTENT.oportunidades;

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
    void getCommercialProposals(
      {
        page: 1,
        page_size: 50,
        search: code,
        sort_by: "proposal_date",
        sort_dir: "desc",
        account_customer_code: code,
      },
      controller.signal,
    )
      .then((page) => {
        if (controller.signal.aborted) return;
        const rows = (page.items ?? []).filter(
          (row) => (row.customer_code || "").trim() === code,
        );
        setItems(rows);
        setTotal(rows.length);
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
  }, [canViewAnalytics, code]);

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
    const query = search.trim().toLowerCase();
    return items.filter((row) => {
      if (statusFilter !== "all") {
        const category = row.status_category ?? "other";
        if (category !== statusFilter) return false;
      }
      return proposalMatchesSearch(row, query);
    });
  }, [items, search, statusFilter]);

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
      {loading ? <CommercialLoadingCard title="Carregando oportunidades…" variant="panel" /> : null}
      {error ? (
        <CommercialEmptyState defaultMessage={error} />
      ) : null}
      {!loading && !error && items.length === 0 ? (
        <CommercialEmptyState
          defaultTitle="Nenhuma OV deste cliente"
          defaultMessage="Não há oportunidades com este código de cliente no recorte atual."
        />
      ) : null}
      {!loading && !error && items.length > 0 ? (
        <>
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
                label: `${copy.statusAll} (${statusCounts.all.toLocaleString("pt-BR")})`,
                active: statusFilter === "all",
                onSelect: () => setStatusFilter("all"),
              },
              {
                id: "open",
                label: `${copy.statusOpen} (${statusCounts.open.toLocaleString("pt-BR")})`,
                active: statusFilter === "open",
                onSelect: () => setStatusFilter("open"),
              },
              {
                id: "won",
                label: `${copy.statusWon} (${statusCounts.won.toLocaleString("pt-BR")})`,
                active: statusFilter === "won",
                onSelect: () => setStatusFilter("won"),
              },
              {
                id: "lost",
                label: `${copy.statusLost} (${statusCounts.lost.toLocaleString("pt-BR")})`,
                active: statusFilter === "lost",
                onSelect: () => setStatusFilter("lost"),
              },
              {
                id: "other",
                label: `${copy.statusOther} (${statusCounts.other.toLocaleString("pt-BR")})`,
                active: statusFilter === "other",
                onSelect: () => setStatusFilter("other"),
              },
            ]}
          />
          <CommercialFilterBarShell embedded layout="inline" ariaLabel={copy.searchLabel}>
            <CommercialTextField
              label={copy.searchLabel}
              hint={CM_HELP.customerDetail.opportunitiesSearch}
              placeholder={copy.searchPlaceholder}
              value={search}
              onChange={setSearch}
            />
          </CommercialFilterBarShell>
          {filteredItems.length === 0 ? (
            <CommercialEmptyState defaultMessage={copy.emptyFiltered} />
          ) : (
            <CommercialProposalsTable
              rows={filteredItems}
              basePath={basePath}
              detailSearch={detailSearch}
              hideCustomerColumn
              showOpenProposal={canViewProposals}
            />
          )}
        </>
      ) : null}
    </CommercialSectionCard>
  );
}
