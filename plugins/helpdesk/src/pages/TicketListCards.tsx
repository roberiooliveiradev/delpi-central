import type { MouseEvent } from "react";

import type { TicketSummary } from "../api/helpdeskApi";
import {
  absoluteDateTimeLabel,
  detailRecordSubtitle,
  statusBadgeVariant,
} from "../presentation/ticketView";
import {
  isModifiedHelpdeskClick,
  ticketDetailPath,
} from "../routing/helpdeskRoute";
import {
  HelpdeskDataCardsGrid,
  HelpdeskRecordCard,
  HelpdeskStatusBadge,
} from "../ui/helpdeskUi";

export function TicketListCards({
  items,
  onOpen,
}: {
  items: TicketSummary[];
  onOpen: (ticketId: number) => void;
}) {
  return (
    <HelpdeskDataCardsGrid
      className="helpdesk-record-list"
      ariaLabel="Chamados em cards"
      empty={items.length === 0 ? "Nenhum chamado neste recorte." : undefined}
    >
      {items.map((row) => {
        const href = ticketDetailPath(row.id);
        const created = absoluteDateTimeLabel(row.created_at);
        const updated = absoluteDateTimeLabel(row.updated_at);
        return (
          <HelpdeskRecordCard
            key={row.id}
            title={row.title.trim() || `Chamado #${row.id}`}
            subtitle={detailRecordSubtitle({
              id: row.id,
              urgency: row.urgency,
              assigned_display_name: row.assigned_display_name,
            })}
            status={<HelpdeskStatusBadge label={row.status} variant={statusBadgeVariant(row.status_id)} />}
            href={href}
            ariaLabel={`Abrir chamado ${row.id}`}
            onNavigate={(event: MouseEvent<HTMLAnchorElement>) => {
              if (isModifiedHelpdeskClick(event)) return;
              event.preventDefault();
              onOpen(row.id);
            }}
            fields={[
              {
                id: "category",
                label: "Categoria",
                value: row.category,
                present: Boolean(row.category.trim()),
              },
              {
                id: "created_at",
                label: "Aberto",
                value: created,
                present: Boolean(created),
              },
              {
                id: "updated_at",
                label: "Atualizado",
                value: updated,
                present: Boolean(updated),
              },
            ]}
          />
        );
      })}
    </HelpdeskDataCardsGrid>
  );
}
