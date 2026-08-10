import { ActionButton, SectionCard } from "@delpi/plugin-ui/index";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActivityTimeline,
  CommercialLoadingCard,
} from "../../../app/commercialUi";
import type { UseCustomerActivitiesResult } from "../hooks/useCustomerActivities";

type CustomerActivityTimelineProps = {
  activities: UseCustomerActivitiesResult;
  canViewActivities: boolean;
  onScheduleFollowUp?: () => void;
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
  activities,
  canViewActivities,
  onScheduleFollowUp,
}: CustomerActivityTimelineProps) {
  const { loading, refreshing, error, hasData, items, reload } = activities;

  return (
    <SectionCard
      title="Timeline de atividades"
      subtitle="Follow-ups e registros da conta (commercial-api)."
      hint={CM_HELP.customerDetail.timeline}
      classNames={cmSectionCardClassNames}
      labels={cmSectionLabels}
    >
      {!canViewActivities ? (
        <p role="status">Você não possui permissão para consultar atividades desta conta.</p>
      ) : null}
      {canViewActivities && loading && !hasData ? (
        <CommercialLoadingCard title="Carregando atividades…" variant="panel" />
      ) : null}
      {canViewActivities && error ? (
        <div role="alert">
          <p>{hasData ? `Não foi possível atualizar: ${error}` : error}</p>
          <ActionButton variant="ghost" onClick={reload} disabled={refreshing}>
            Tentar novamente
          </ActionButton>
        </div>
      ) : null}
      {canViewActivities && hasData ? (
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
      {onScheduleFollowUp ? (
        <div className="cm-nav-row">
          <ActionButton variant="primary" onClick={onScheduleFollowUp}>
            Agendar follow-up
          </ActionButton>
        </div>
      ) : null}
    </SectionCard>
  );
}
