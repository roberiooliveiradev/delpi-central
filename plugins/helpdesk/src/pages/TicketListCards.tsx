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
  const photoEntries = useMemo(() => {
    const entries: { directoryUserId?: string; hasPhoto?: boolean }[] = [];
    for (const row of items) {
      const requesterId = (row.requester_directory_user_id || "").trim();
      if (requesterId) {
        entries.push({
          directoryUserId: requesterId,
          hasPhoto: Boolean(row.requester_has_photo),
        });
      }
      const assignedId = (row.assigned_directory_user_id || "").trim();
      if (assignedId) {
        entries.push({
          directoryUserId: assignedId,
          hasPhoto: Boolean(row.assigned_has_photo),
        });
      }
    }
    return entries;
  }, [items]);
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
        const technician = (row.assigned_display_name ?? "").trim();
        const requesterDirectoryId = (row.requester_directory_user_id || "").trim();
        const assignedDirectoryId = (row.assigned_directory_user_id || "").trim();
        const requesterPhotoSrc =
          (requesterDirectoryId ? photoFor(requesterDirectoryId) : null) ||
          (preferMyPhoto && !requesterDirectoryId ? myPhotoUrl : null) ||
          null;
        const assignedPhotoSrc = assignedDirectoryId ? photoFor(assignedDirectoryId) : null;
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
                      directoryUserId: requesterDirectoryId,
                      displayName: requester,
                    })}
                    src={requesterPhotoSrc}
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
                value: technician ? (
                  <HelpdeskEntityAvatarLabel
                    name={technician}
                    colorKey={resolveAvatarColorKey({
                      directoryUserId: assignedDirectoryId,
                      displayName: technician,
                    })}
                    src={assignedPhotoSrc}
                    size="sm"
                  />
                ) : (
                  "—"
                ),
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
