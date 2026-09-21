import { absoluteDateTimeLabel, statusBadgeVariant } from "../presentation/ticketView";
import {
  resolveVisibleColumns,
  type TicketListColumnDefinition,
  type TicketListColumnPreference,
} from "../presentation/ticketListViewModel";
import type { TicketSummary } from "../api/helpdeskApi";
import { helpTooltips } from "../content/helpTooltips";
import { HelpdeskDataTable, HelpdeskStatusBadge } from "../ui/helpdeskUi";

export function TicketListTable({
  items,
  loading,
  sort,
  onSortChange,
  onOpen,
  columnPreferences,
}: {
  items: TicketSummary[];
  loading: boolean;
  sort: { key: string; direction: "asc" | "desc" };
  onSortChange: (columnKey: string) => void;
  onOpen: (ticketId: number) => void;
  /** When omitted, solicitante defaults from the catalog are used. */
  columnPreferences?: TicketListColumnPreference[];
}) {
  const columns = resolveVisibleColumns(columnPreferences).map((definition) =>
    toDataTableColumn(definition),
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
      onRowClick={(row) => onOpen(row.id)}
      columns={columns}
    />
  );
}

function toDataTableColumn(definition: TicketListColumnDefinition) {
  return {
    key: definition.key,
    header: definition.header,
    headerHint: helpTooltips.columns[definition.key as keyof typeof helpTooltips.columns],
    sortable: definition.sortable,
    render: (row: TicketSummary) => renderColumn(definition.key, row),
  };
}

function renderColumn(key: TicketListColumnDefinition["key"], row: TicketSummary) {
  switch (key) {
    case "id":
      return String(row.id);
    case "title":
      return row.title;
    case "status":
      return <HelpdeskStatusBadge label={row.status} variant={statusBadgeVariant(row.status_id)} />;
    case "category":
      return row.category;
    case "urgency":
      return row.urgency;
    case "assigned":
      return row.assigned_display_name;
    case "created_at":
      return absoluteDateTimeLabel(row.created_at);
    case "updated_at":
      return absoluteDateTimeLabel(row.updated_at);
    case "solved_at":
      return absoluteDateTimeLabel(row.solved_at ?? "");
    case "closed_at":
      return absoluteDateTimeLabel(row.closed_at ?? "");
    case "requester":
    case "entity":
    case "last_editor":
      return "";
    default:
      return "";
  }
}
