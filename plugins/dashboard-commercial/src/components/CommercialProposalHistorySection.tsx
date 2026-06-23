import type { DataTableColumn } from "./DataTable";
import { DataTable } from "./DataTable";
import type { CommercialProposalHistoryEvent } from "../types/commercial";
import { formatDisplayDate } from "../utils/dates";

type CommercialProposalHistorySectionProps = {
  items: CommercialProposalHistoryEvent[];
  loading?: boolean;
};

const columns: DataTableColumn<CommercialProposalHistoryEvent>[] = [
  {
    key: "revision",
    header: "Rev.",
    render: (row) => row.revision || "—",
  },
  {
    key: "process",
    header: "Processo",
    render: (row) => row.process_label || row.process_code || "—",
  },
  {
    key: "stage",
    header: "Estágio",
    render: (row) => row.stage_label || row.stage_code || "—",
  },
  {
    key: "start",
    header: "Início",
    render: (row) => formatDisplayDate(row.start_date),
  },
  {
    key: "end",
    header: "Fim",
    render: (row) => formatDisplayDate(row.end_date),
  },
  {
    key: "status",
    header: "Status",
    render: (row) => row.status_label || row.status || "—",
  },
  {
    key: "duration",
    header: "Duração",
    render: (row) => row.duration_display || "—",
  },
];

export function CommercialProposalHistorySection({
  items,
  loading = false,
}: CommercialProposalHistorySectionProps) {
  return (
    <DataTable
      columns={columns}
      rows={items}
      rowKey={(row, index) =>
        `${row.revision}-${row.process_code}-${row.stage_code}-${index}`
      }
      loading={loading}
      emptyMessage="Nenhum evento de histórico encontrado para esta OV."
    />
  );
}
