import { useCallback, useEffect, useMemo, useState } from "react";

import { listSellerPortfolioAudit } from "../../../api/commercialPortfolioApi";
import { useCommercialPortfolioSync } from "../../../app/CommercialRealtimeProvider";
import { useDirectoryUserLabels } from "../../../app/useDirectoryUserLabels";
import {
  CommercialSectionCard,
  CommercialSelectField,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { PORTFOLIO_AUDIT_CONTENT } from "../../../content/portfolioAuditContent";
import type { SellerPortfolio, SellerPortfolioAuditEvent } from "../../../types/portfolio";
import { SellerPortfolioAuditTimeline } from "../../seller-portfolios/SellerPortfolioAuditTimeline";

type MyPortfolioAuditSectionProps = {
  /** Filtro Carteira da página (null = Todas). */
  sellerIdFilter: string | null;
  myPortfolios: SellerPortfolio[];
  /** Quando team scope, universo do seletor «Todas». */
  filterablePortfolios: SellerPortfolio[];
};

/**
 * Histórico da carteira em Minha Carteira (membro).
 * portfolioId = filtro atual; se «Todas», exige escolha explícita quando há N carteiras.
 */
export function MyPortfolioAuditSection({
  sellerIdFilter,
  myPortfolios,
  filterablePortfolios,
}: MyPortfolioAuditSectionProps) {
  const candidatePortfolios = useMemo(() => {
    if (myPortfolios.length > 0) return myPortfolios;
    return filterablePortfolios;
  }, [filterablePortfolios, myPortfolios]);

  const [manualPortfolioId, setManualPortfolioId] = useState<string | null>(null);

  const needsManualSelect = !sellerIdFilter && candidatePortfolios.length > 1;

  useEffect(() => {
    if (sellerIdFilter) {
      setManualPortfolioId(null);
      return;
    }
    if (candidatePortfolios.length === 1) {
      setManualPortfolioId(candidatePortfolios[0]?.id ?? null);
      return;
    }
    if (
      manualPortfolioId &&
      !candidatePortfolios.some((item) => item.id === manualPortfolioId)
    ) {
      setManualPortfolioId(null);
    }
  }, [candidatePortfolios, manualPortfolioId, sellerIdFilter]);

  const auditPortfolioId = sellerIdFilter ?? manualPortfolioId ?? candidatePortfolios[0]?.id ?? null;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<SellerPortfolioAuditEvent[]>([]);

  const reloadAudit = useCallback(
    (options?: { signal?: AbortSignal; silent?: boolean }) => {
      if (!auditPortfolioId) {
        setEvents([]);
        setError(null);
        setLoading(false);
        return;
      }
      if (!options?.silent) setLoading(true);
      setError(null);
      listSellerPortfolioAudit(auditPortfolioId, {
        page: 1,
        pageSize: 50,
        signal: options?.signal,
      })
        .then((page) => {
          if (options?.signal?.aborted) return;
          setEvents(page.items);
        })
        .catch((err: unknown) => {
          if (options?.signal?.aborted) return;
          setError(err instanceof Error ? err.message : "Erro ao carregar histórico.");
        })
        .finally(() => {
          if (!options?.signal?.aborted) setLoading(false);
        });
    },
    [auditPortfolioId],
  );

  useEffect(() => {
    const controller = new AbortController();
    reloadAudit({ signal: controller.signal });
    return () => controller.abort();
  }, [reloadAudit]);

  useCommercialPortfolioSync(
    () => {
      reloadAudit({ silent: true });
    },
    { enabled: Boolean(auditPortfolioId), portfolioId: auditPortfolioId },
  );

  const directoryUserIds = useMemo(() => {
    const ids = new Set<string>();
    for (const event of events) {
      const actor = event.actor_user_id?.trim();
      if (actor) ids.add(actor);
      const payloadUser =
        typeof event.payload?.user_id === "string" ? event.payload.user_id.trim() : "";
      if (payloadUser) ids.add(payloadUser);
    }
    return [...ids];
  }, [events]);
  const { labelFor: directoryLabelFor } = useDirectoryUserLabels(directoryUserIds);

  if (candidatePortfolios.length === 0) {
    return null;
  }

  return (
    <div className="cm-customers-page__audit">
      {needsManualSelect ? (
        <CommercialSectionCard
          title={PORTFOLIO_AUDIT_CONTENT.selectPortfolioLabel}
          subtitle={PORTFOLIO_AUDIT_CONTENT.selectPortfolioHint}
          hint={CM_HELP.customers.portfolioAudit}
        >
          <CommercialSelectField
            label={PORTFOLIO_AUDIT_CONTENT.selectPortfolioLabel}
            hint={CM_HELP.customers.portfolioAudit}
            options={candidatePortfolios.map((portfolio) => ({
              value: portfolio.id,
              label: portfolio.display_name,
            }))}
            value={manualPortfolioId ?? ""}
            onChange={(next) => setManualPortfolioId(next || null)}
            allowEmpty
            emptyLabel={PORTFOLIO_AUDIT_CONTENT.selectPortfolioPlaceholder}
            searchable={candidatePortfolios.length > 8}
          />
        </CommercialSectionCard>
      ) : null}

      {auditPortfolioId ? (
        <SellerPortfolioAuditTimeline
          loading={loading}
          error={error}
          events={events}
          directoryLabelFor={directoryLabelFor}
          onRetry={() => reloadAudit()}
          title={PORTFOLIO_AUDIT_CONTENT.titleMember}
          subtitle={PORTFOLIO_AUDIT_CONTENT.subtitleMember}
          hint={CM_HELP.customers.portfolioAudit}
          collapsible
          defaultOpen={false}
        />
      ) : null}
    </div>
  );
}
