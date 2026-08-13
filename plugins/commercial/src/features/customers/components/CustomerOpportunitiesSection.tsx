import { useEffect, useState } from "react";

import { getCommercialProposals } from "../../../api/analyticsApi";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialSectionCard,
} from "../../../app/commercialUi";
import { navigatePluginView } from "../../../app/pluginNavigation";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { CM_HELP } from "../../../content/helpTooltips";
import type { CommercialProposal } from "../../../types/analytics";
import { CommercialProposalsTable } from "../../analytics/components/CommercialProposalsTable";

type CustomerOpportunitiesSectionProps = {
  basePath: string;
  customerCode: string;
  canViewAnalytics: boolean;
};

/**
 * Lista real de OVs do cliente (mesmo contrato da página global, filtrada por código).
 */
export function CustomerOpportunitiesSection({
  basePath,
  customerCode,
  canViewAnalytics,
}: CustomerOpportunitiesSectionProps) {
  const [items, setItems] = useState<CommercialProposal[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const code = customerCode.trim();
  const detailSearch = code
    ? `?${new URLSearchParams({ search: code }).toString()}`
    : undefined;

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

  if (!canViewAnalytics) {
    return (
      <CommercialEmptyState
        title={ANALYTICS_CONTENT.oportunidades.title}
        message="Você não possui permissão para consultar oportunidades."
      />
    );
  }

  if (!code) {
    return (
      <CommercialEmptyState
        title={ANALYTICS_CONTENT.oportunidades.title}
        message="Cliente sem código para filtrar oportunidades."
      />
    );
  }

  return (
    <CommercialSectionCard
      title={`Oportunidades (${total.toLocaleString("pt-BR")})`}
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
        <CommercialProposalsTable
          rows={items}
          basePath={basePath}
          detailSearch={detailSearch}
          hideCustomerColumn
        />
      ) : null}
    </CommercialSectionCard>
  );
}
