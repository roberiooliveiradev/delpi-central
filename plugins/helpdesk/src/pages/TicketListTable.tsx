import { relativeTimeLabel, statusBadgeVariant } from "../presentation/ticketView";
import type { TicketSummary } from "../api/helpdeskApi";
import { HelpdeskDataTable, HelpdeskStatusBadge } from "../ui/helpdeskUi";

export function TicketListTable({
  items,
  loading,
  sort,
  onSortChange,
  onOpen,
}: {
  items: TicketSummary[];
  loading: boolean;
  sort: { key: string; direction: "asc" | "desc" };
  onSortChange: (columnKey: string) => void;
  onOpen: (ticketId: number) => void;
}) {
  const now = new Date();
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
      columns={[
        { key: "id", header: "Chamado", sortable: true, render: (row) => String(row.id) },
        { key: "title", header: "Título", sortable: true, render: (row) => row.title },
        {
          key: "status",
          header: "Status",
          sortable: true,
          render: (row) => <HelpdeskStatusBadge label={row.status} variant={statusBadgeVariant(row.status)} />,
        },
        { key: "category", header: "Categoria", sortable: true, render: (row) => row.category },
        { key: "urgency", header: "Urgência", sortable: true, render: (row) => row.urgency },
        { key: "assigned", header: "Técnico", render: (row) => row.assigned_display_name },
        {
          key: "created_at",
          header: "Aberto",
          sortable: true,
          render: (row) => relativeTimeLabel(row.created_at, now),
        },
        {
          key: "updated_at",
          header: "Atualizado",
          sortable: true,
          render: (row) => relativeTimeLabel(row.updated_at, now),
        },
      ]}
    />
  );
}
