import type { DataTableColumn } from "@delpi/plugin-ui/index";

import { CommercialDataTable } from "../../../app/commercialUi";
import { navigateAnalyticsOpportunityDetail } from "../../../app/pluginNavigation";
import type { CommercialProposal } from "../../../types/analytics";
import { formatDisplayDate } from "../../../utils/dates";

export type CommercialProposalsTableOptions = {
  basePath: string;
  /** Query string preserved when opening OV detail (back navigation). */
  detailSearch?: string;
  /** When true, omit Cliente column (account context). */
  hideCustomerColumn?: boolean;
};

/** Colunas canônicas da lista de OVs (página global e Conta). */
export function buildCommercialProposalColumns(
  options: CommercialProposalsTableOptions,
): DataTableColumn<CommercialProposal>[] {
  const openDetail = (row: CommercialProposal) =>
    navigateAnalyticsOpportunityDetail(row.proposal_number, {
      basePath: options.basePath,
      search: options.detailSearch,
    });

  const columns: DataTableColumn<CommercialProposal>[] = [
    {
      key: "ov",
      header: "OV",
      render: (row) => (
        <button type="button" className="cm-link-button" onClick={() => openDetail(row)}>
          {row.proposal_number}
        </button>
      ),
    },
    { key: "rev", header: "Rev.", render: (row) => row.revision || "—" },
  ];

  if (!options.hideCustomerColumn) {
    columns.push({
      key: "customer",
      header: "Cliente",
      render: (row) => row.customer_code || "—",
    });
  }

  columns.push(
    {
      key: "status",
      header: "Status",
      render: (row) => row.status_label || row.status_code || "—",
    },
    { key: "stage", header: "Etapa", render: (row) => row.stage || "—" },
    {
      key: "date",
      header: "Data",
      render: (row) => formatDisplayDate(row.proposal_date),
    },
  );

  return columns;
}

type CommercialProposalsTableProps = CommercialProposalsTableOptions & {
  rows: CommercialProposal[];
  onRowClick?: (row: CommercialProposal) => void;
};

export function CommercialProposalsTable({
  rows,
  basePath,
  detailSearch,
  hideCustomerColumn,
  onRowClick,
}: CommercialProposalsTableProps) {
  const columns = buildCommercialProposalColumns({
    basePath,
    detailSearch,
    hideCustomerColumn,
  });

  return (
    <CommercialDataTable
      rows={rows}
      columns={columns}
      rowKey={(row) => `${row.branch}-${row.proposal_number}-${row.revision}`}
      layout="section"
      onRowClick={
        onRowClick ??
        ((row) =>
          navigateAnalyticsOpportunityDetail(row.proposal_number, {
            basePath,
            search: detailSearch,
          }))
      }
    />
  );
}
