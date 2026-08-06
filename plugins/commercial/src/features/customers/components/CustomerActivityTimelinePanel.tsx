import { useEffect, useState } from "react";
import { ActionButton, SectionCard } from "@delpi/plugin-ui/index";

import { listCustomerActivities, type CommercialActivityDto } from "../../../api/worklistApi";
import {
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActivityTimeline,
  CommercialLoadingCard,
} from "../../../app/commercialUi";

type CustomerActivityTimelineProps = {
  codigo: string;
  loja: string;
  basePath: string;
};

function formatWhen(iso?: string | null): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function CustomerActivityTimelinePanel({
  codigo,
  loja,
  basePath,
}: CustomerActivityTimelineProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<CommercialActivityDto[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    listCustomerActivities(codigo, loja, controller.signal)
      .then((rows) => setItems(rows))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar timeline.");
        setItems([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [codigo, loja]);

  return (
    <SectionCard
      title="Timeline de atividades"
      subtitle="Follow-ups e registros da conta (commercial-api)."
      classNames={cmSectionCardClassNames}
      labels={cmSectionLabels}
    >
      {loading ? <CommercialLoadingCard title="Carregando atividades…" variant="panel" /> : null}
      {error ? <p role="alert">{error}</p> : null}
      {!loading ? (
        <CommercialActivityTimeline
          items={items.map((item) => ({
            id: item.id,
            title: item.subject || item.activity_type,
            occurredAt: item.occurred_at,
            timeLabel: formatWhen(item.occurred_at),
            detail: item.body || undefined,
            tone: item.activity_type === "system" ? "info" : "default",
          }))}
          emptyMessage="Ainda não há atividades nesta conta. Registre um follow-up no Meu dia."
          aria-label="Timeline da conta"
        />
      ) : null}
      <div className="cm-nav-row" style={{ marginTop: 12 }}>
        <ActionButton
          variant="ghost"
          onClick={() => window.location.assign("/apps/propostas-comerciais")}
        >
          Propostas →
        </ActionButton>
        <ActionButton
          variant="ghost"
          onClick={() => window.location.assign("/apps/dashboard-commercial")}
        >
          Dashboard OV →
        </ActionButton>
        <ActionButton
          variant="ghost"
          onClick={() => {
            window.location.assign(`${basePath}/open-orders`);
          }}
        >
          Pedidos filtrados →
        </ActionButton>
      </div>
    </SectionCard>
  );
}
