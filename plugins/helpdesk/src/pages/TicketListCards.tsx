import { useMemo, type MouseEvent } from "react";
import { resolveAvatarColorKey } from "@delpi/plugin-ui/index";

import type { TicketSummary } from "../api/helpdeskApi";
import {
  absoluteDateTimeLabel,
  relativeTimeLabel,
  statusBadgeVariant,
} from "../presentation/ticketView";
import { useDirectoryUserPhotoUrls } from "../presentation/useDirectoryUserPhotoUrls";
import {
  isModifiedHelpdeskClick,
  ticketDetailPath,
} from "../routing/helpdeskRoute";
import {
  HelpdeskDataCardsGrid,
  HelpdeskEntityAvatarLabel,
  HelpdeskRecordCard,
  HelpdeskStatusBadge,
} from "../ui/helpdeskUi";

export function TicketListCards({
  items,
  onOpen,
  myPhotoUrl,
  preferMyPhoto = false,
}: {
  items: TicketSummary[];
  onOpen: (ticketId: number) => void;
  myPhotoUrl?: string | null;
  preferMyPhoto?: boolean;
}) {
  const now = new Date();
  const photoEntries = useMemo(
    () =>
      items.map((row) => ({
        directoryUserId: (row.requester_directory_user_id || "").trim() || undefined,
        hasPhoto: Boolean(row.requester_has_photo) || preferMyPhoto,
      })),
    [items, preferMyPhoto],
  );
  const { photoFor } = useDirectoryUserPhotoUrls(photoEntries);

  return (
    <HelpdeskDataCardsGrid
      className="helpdesk-record-list"
      ariaLabel="Chamados em lista"
      empty={items.length === 0 ? "Nenhum chamado neste recorte." : undefined}
    >
      {items.map((row) => {
        const href = ticketDetailPath(row.id);
        const urgency = row.urgency.trim();
        const updatedAbs = absoluteDateTimeLabel(row.updated_at);
        const updatedRel = relativeTimeLabel(row.updated_at, now) || updatedAbs;
        const requester = (row.requester_display_name ?? "").trim();
        const technician = row.assigned_display_name.trim();
        const directoryId = (row.requester_directory_user_id || "").trim();
        const photoSrc =
          (directoryId ? photoFor(directoryId) : null) ||
          (preferMyPhoto || row.requester_has_photo ? myPhotoUrl : null) ||
          null;
        return (
          <HelpdeskRecordCard
            key={row.id}
            title={row.title.trim() || `Chamado #${row.id}`}
            subtitle={`#${row.id}${urgency ? ` · ${urgency}` : ""}`}
            status={
              <HelpdeskStatusBadge label={row.status} variant={statusBadgeVariant(row.status_id)} />
            }
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
                id: "requester",
                label: "Solicitante",
                value: requester ? (
                  <HelpdeskEntityAvatarLabel
                    name={requester}
                    colorKey={resolveAvatarColorKey({
                      directoryUserId: directoryId,
                      displayName: requester,
                    })}
                    src={photoSrc}
                    size="sm"
                  />
                ) : (
                  ""
                ),
                present: Boolean(requester),
              },
              {
                id: "assigned",
                label: "Técnico",
                value: technician || "—",
                present: true,
              },
              {
                id: "updated_at",
                label: "Atualizado",
                value: (
                  <time dateTime={row.updated_at} title={updatedAbs || undefined}>
                    {updatedRel}
                  </time>
                ),
                present: Boolean(updatedRel),
              },
            ]}
          />
        );
      })}
    </HelpdeskDataCardsGrid>
  );
}
