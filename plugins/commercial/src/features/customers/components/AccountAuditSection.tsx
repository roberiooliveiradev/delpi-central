import { useCallback, useEffect, useMemo, useState } from "react";

import { listCustomerAccountAudit } from "../../../api/customerAccountAuditApi";
import { useDirectoryUserLabels } from "../../../app/useDirectoryUserLabels";
import { CM_HELP } from "../../../content/helpTooltips";
import type { SellerPortfolioAuditEvent } from "../../../types/portfolio";
import { SellerPortfolioAuditTimeline } from "../../seller-portfolios/SellerPortfolioAuditTimeline";

type AccountAuditSectionProps = {
  codigo: string;
  loja: string;
  refreshKey?: number;
};

/**
 * Timeline de auditoria da Conta (contatos / avatar) — mesmo chrome da carteira.
 */
export function AccountAuditSection({
  codigo,
  loja,
  refreshKey = 0,
}: AccountAuditSectionProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<SellerPortfolioAuditEvent[]>([]);

  const reloadAudit = useCallback(
    (options?: { signal?: AbortSignal; silent?: boolean }) => {
      const code = codigo.trim();
      const store = loja.trim();
      if (!code || !store) {
        setEvents([]);
        return;
      }
      if (!options?.silent) setLoading(true);
      setError(null);
      listCustomerAccountAudit(code, store, {
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
          setError(
            err instanceof Error ? err.message : "Erro ao carregar histórico.",
          );
        })
        .finally(() => {
          if (!options?.signal?.aborted) setLoading(false);
        });
    },
    [codigo, loja],
  );

  useEffect(() => {
    const controller = new AbortController();
    reloadAudit({ signal: controller.signal });
    return () => controller.abort();
  }, [reloadAudit, refreshKey]);

  const directoryUserIds = useMemo(() => {
    const ids = new Set<string>();
    for (const event of events) {
      const actor = event.actor_user_id?.trim();
      if (actor) ids.add(actor);
    }
    return [...ids];
  }, [events]);
  const { labelFor: directoryLabelFor } = useDirectoryUserLabels(directoryUserIds);

  return (
    <SellerPortfolioAuditTimeline
      loading={loading}
      error={error}
      events={events}
      directoryLabelFor={directoryLabelFor}
      onRetry={() => reloadAudit()}
      title="Histórico da conta"
      subtitle="Alterações em contatos e avatar desta conta."
      hint={CM_HELP.customerDetail.contacts}
    />
  );
}
