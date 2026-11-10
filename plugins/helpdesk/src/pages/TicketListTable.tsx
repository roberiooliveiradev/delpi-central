import { useMemo, type MouseEvent, type ReactNode } from "react";
import { resolveAvatarColorKey } from "@delpi/plugin-ui/index";

import { absoluteDateTimeLabel, relativeTimeLabel, statusBadgeVariant } from "../presentation/ticketView";
import {
  cellTextForColumn,
  resolveVisibleColumns,
  type TicketListColumnDefinition,
  type TicketListColumnPreference,
} from "../presentation/ticketListViewModel";
import type { TicketSummary } from "../api/helpdeskApi";
import { helpTooltips } from "../content/helpTooltips";
import { useDirectoryUserPhotoUrls } from "../presentation/useDirectoryUserPhotoUrls";
import {
  followHelpdeskPath,
  isModifiedHelpdeskClick,
  ticketDetailPath,
} from "../routing/helpdeskRoute";
import {
  HelpdeskDataTable,
  HelpdeskEntityAvatarLabel,
  HelpdeskStatusBadge,
  helpdeskDataTableClassNames,
} from "../ui/helpdeskUi";

function eventFromTicketLink(event: { target: EventTarget | null }): boolean {
  const node = event.target;
  if (!(node instanceof Node)) return false;
  const element = node instanceof Element ? node : node.parentElement;
  return Boolean(element?.closest("a"));
}

export function TicketListTable({
  items,
  loading,
  sort,
  onSortChange,
  onOpen,
  columnPreferences,
  myPhotoUrl,
  preferMyPhoto = false,
}: {
  items: TicketSummary[];
  loading: boolean;
  sort: { key: string; direction: "asc" | "desc" };
  onSortChange: (columnKey: string) => void;
  onOpen: (ticketId: number) => void;
  /** When omitted, solicitante defaults from the catalog are used. */
  columnPreferences?: TicketListColumnPreference[];
  /** Authenticated Minha DELPI person-profile photo (blob URL). */
  myPhotoUrl?: string | null;
  /** When true (ex.: filtro Meus chamados), use myPhotoUrl if directory photo is missing. */
  preferMyPhoto?: boolean;
}) {
  const photoEntries = useMemo(
    () =>
      items.map((row) => ({
        directoryUserId: (row.requester_directory_user_id || "").trim() || undefined,
        hasPhoto: Boolean(row.requester_has_photo) || preferMyPhoto,
      })),
    [items, preferMyPhoto],
  );
  const { photoFor } = useDirectoryUserPhotoUrls(photoEntries);

  const columns = resolveVisibleColumns(columnPreferences).map((definition) =>
    toDataTableColumn(definition, photoFor, myPhotoUrl, preferMyPhoto),
  );

  return (
    <HelpdeskDataTable
      layout="scroll"
      compact
      loading={loading}
      rows={items}
      rowKey={(row) => String(row.id)}
      sortKey={sort.key}
      sortDirection={sort.direction}
      onSortChange={onSortChange}
      getRowClassName={() => helpdeskDataTableClassNames.rowClickable}
      getRowProps={(row) => ({
        tabIndex: 0,
        role: "link",
        onClick: (event) => {
          if (eventFromTicketLink(event)) return;
          const path = ticketDetailPath(row.id);
          if (isModifiedHelpdeskClick(event)) {
            followHelpdeskPath(path, event);
            return;
          }
          onOpen(row.id);
        },
        onAuxClick: (event) => {
          if (event.button !== 1) return;
          if (eventFromTicketLink(event)) return;
          event.preventDefault();
          followHelpdeskPath(ticketDetailPath(row.id), event);
        },
        onKeyDown: (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onOpen(row.id);
          }
        },
      })}
      columns={columns}
    />
  );
}

function toDataTableColumn(
  definition: TicketListColumnDefinition,
  photoFor: (directoryUserId: string | null | undefined) => string | null,
  myPhotoUrl?: string | null,
  preferMyPhoto = false,
) {
  return {
    key: definition.key,
    header: definition.header,
    headerHint: helpTooltips.columns[definition.key as keyof typeof helpTooltips.columns],
    sortable: definition.sortable,
    render: (row: TicketSummary) =>
      renderColumn(definition.key, row, photoFor, myPhotoUrl, preferMyPhoto),
  };
}

function TicketDetailLink({ ticketId, children }: { ticketId: number; children: ReactNode }) {
  const href = ticketDetailPath(ticketId);
  return (
    <a
      className="helpdesk-ticket-link"
      href={href}
      onClick={(event: MouseEvent<HTMLAnchorElement>) => {
        event.stopPropagation();
        if (isModifiedHelpdeskClick(event)) return;
        event.preventDefault();
        followHelpdeskPath(href);
      }}
    >
      {children}
    </a>
  );
}

function DateCell({ value }: { value: string }) {
  const absolute = absoluteDateTimeLabel(value);
  const relative = relativeTimeLabel(value, new Date()) || absolute;
  if (!relative) return "";
  return (
    <time dateTime={value} title={absolute || undefined} aria-label={absolute || relative}>
      {relative}
    </time>
  );
}

function requesterPhotoSrc(
  row: TicketSummary,
  photoFor: (directoryUserId: string | null | undefined) => string | null,
  myPhotoUrl?: string | null,
  preferMyPhoto = false,
): string | null {
  const directoryId = (row.requester_directory_user_id || "").trim();
  if (directoryId) {
    const fromDirectory = photoFor(directoryId);
    if (fromDirectory) return fromDirectory;
  }
  if (preferMyPhoto && myPhotoUrl) return myPhotoUrl;
  if (row.requester_has_photo && myPhotoUrl) return myPhotoUrl;
  return null;
}

function renderColumn(
  key: TicketListColumnDefinition["key"],
  row: TicketSummary,
  photoFor: (directoryUserId: string | null | undefined) => string | null = () => null,
  myPhotoUrl?: string | null,
  preferMyPhoto = false,
) {
  switch (key) {
    case "id":
      return <TicketDetailLink ticketId={row.id}>{String(row.id)}</TicketDetailLink>;
    case "title":
      return <TicketDetailLink ticketId={row.id}>{row.title}</TicketDetailLink>;
    case "status":
      return <HelpdeskStatusBadge label={row.status} variant={statusBadgeVariant(row.status_id)} />;
    case "category":
      return row.category;
    case "urgency":
      return row.urgency;
    case "assigned":
      return row.assigned_display_name;
    case "requester": {
      const name = (row.requester_display_name ?? "").trim();
      if (!name) return "";
      const directoryId = (row.requester_directory_user_id || "").trim();
      return (
        <HelpdeskEntityAvatarLabel
          name={name}
          colorKey={resolveAvatarColorKey({
            directoryUserId: directoryId,
            displayName: name,
          })}
          src={requesterPhotoSrc(row, photoFor, myPhotoUrl, preferMyPhoto)}
          size="sm"
        />
      );
    }
    case "created_at":
      return <DateCell value={row.created_at} />;
    case "updated_at":
      return <DateCell value={row.updated_at} />;
    case "solved_at":
      return <DateCell value={row.solved_at ?? ""} />;
    case "closed_at":
      return <DateCell value={row.closed_at ?? ""} />;
    default:
      // Plain-text cells share the canonical formatter (entity/last_editor…).
      return cellTextForColumn(row, key);
  }
}
