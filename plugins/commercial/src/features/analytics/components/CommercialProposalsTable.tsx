import type { DataTableColumn } from "@delpi/plugin-ui/index";
import { useMemo, useState } from "react";

import {
  CommercialDataTable,
  CommercialEntityLink,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import {
  buildAnalyticsOpportunityDetailHref,
  navigateAnalyticsOpportunityDetail,
} from "../../../app/pluginNavigation";
import { opportunityLinkTitle } from "../../../content/entityLinkHints";
import type {
  CommercialProposal,
  CommercialProposalStatusCategory,
} from "../../../types/analytics";
import {
  PROPOSALS_DOCUMENTS_COLUMN_HELP,
  withColumnHelp,
} from "../../../utils/customersColumnHelp";
import { formatDisplayDate } from "../../../utils/dates";
import {
  nextTableSortState,
  sortTableRows,
  type TableSortDirection,
} from "../../../utils/sortTableRows";
import { OpenProposalFromOpportunityButton } from "./OpenProposalFromOpportunityButton";

export type CommercialProposalsTableOptions = {
  basePath: string;
  /** Query string preserved when opening OV detail (back navigation). */
  detailSearch?: string;
  /** When true, omit Cliente column (account context). */
  hideCustomerColumn?: boolean;
  /** CTA Abrir proposta (ADY) quando o usuário tem proposals.view. */
  showOpenProposal?: boolean;
};

function statusBadgeVariant(
  category: CommercialProposalStatusCategory | null | undefined,
): "success" | "danger" | "info" | "neutral" {
  switch (category) {
    case "won":
      return "success";
    case "lost":
      return "danger";
    case "open":
      return "info";
    default:
      return "neutral";
  }
}

/** Colunas canônicas da lista de OVs (página global e Conta). */
export function buildCommercialProposalColumns(
  options: CommercialProposalsTableOptions,
): DataTableColumn<CommercialProposal>[] {
  const columns: DataTableColumn<CommercialProposal>[] = [
    {
      key: "ov",
      header: "OV",
      sortable: true,
      sortValue: (row) => row.proposal_number,
      interactive: true,
      rowClick: "stop",
      render: (row) => {
        const href = buildAnalyticsOpportunityDetailHref(row.proposal_number, {
          basePath: options.basePath,
          search: options.detailSearch,
        });
        if (!href) {
          return <span className="cm-proposals-table__ov">{row.proposal_number}</span>;
        }
        return (
          <CommercialEntityLink
            href={href}
            title={opportunityLinkTitle(row.proposal_number)}
            className="cm-link-button cm-proposals-table__ov"
            onNavigate={() =>
              navigateAnalyticsOpportunityDetail(row.proposal_number, {
                basePath: options.basePath,
                search: options.detailSearch,
              })
            }
          >
            {row.proposal_number}
          </CommercialEntityLink>
        );
      },
    },
    {
      key: "rev",
      header: "Rev.",
      sortable: true,
      sortValue: (row) => row.revision,
      render: (row) => row.revision || "—",
    },
  ];

  if (!options.hideCustomerColumn) {
    columns.push({
      key: "customer",
      header: "Cliente",
      sortable: true,
      sortValue: (row) => row.customer_code,
      render: (row) => row.customer_code || "—",
    });
  }

  columns.push(
    {
      key: "status",
      header: "Status",
      sortable: true,
      sortValue: (row) => row.status_label || row.status_code || "",
      render: (row) => (
        <CommercialStatusBadge
          label={row.status_label || row.status_code || "—"}
          variant={statusBadgeVariant(row.status_category)}
        />
      ),
    },
    {
      key: "stage",
      header: "Etapa",
      sortable: true,
      sortValue: (row) => row.stage,
      render: (row) => row.stage || "—",
    },
    {
      key: "date",
      header: "Data",
      sortable: true,
      sortValue: (row) => row.proposal_date,
      render: (row) => formatDisplayDate(row.proposal_date),
    },
  );

  if (options.showOpenProposal) {
    columns.push({
      key: "proposal-doc",
      header: "Proposta",
      interactive: true,
      rowClick: "stop",
      render: (row) => (
        <OpenProposalFromOpportunityButton
          basePath={options.basePath}
          opportunityNumber={row.proposal_number}
        />
      ),
    });
  }

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
  showOpenProposal,
  onRowClick,
}: CommercialProposalsTableProps) {
  const [sortKey, setSortKey] = useState<string>("date");
  const [sortDirection, setSortDirection] = useState<TableSortDirection>("desc");

  const baseColumns = useMemo(
    () =>
      buildCommercialProposalColumns({
        basePath,
        detailSearch,
        hideCustomerColumn,
        showOpenProposal,
      }),
    [basePath, detailSearch, hideCustomerColumn, showOpenProposal],
  );
  const columns = withColumnHelp(baseColumns, PROPOSALS_DOCUMENTS_COLUMN_HELP);
  const sortedRows = useMemo(
    () => sortTableRows(rows, columns, sortKey, sortDirection),
    [columns, rows, sortDirection, sortKey],
  );

  return (
    <CommercialDataTable
      rows={sortedRows}
      columns={columns}
      rowKey={(row) => `${row.branch}-${row.proposal_number}-${row.revision}`}
      layout="section"
      sortKey={sortKey}
      sortDirection={sortDirection}
      onSortChange={(key) => {
        const next = nextTableSortState(sortKey, sortDirection, key);
        setSortKey(next.sortKey);
        setSortDirection(next.sortDirection);
      }}
      onRowClick={
        onRowClick ??
        ((row) =>
          navigateAnalyticsOpportunityDetail(row.proposal_number, {
            basePath,
            search: detailSearch,
          }))
      }
      rowClickRole="button"
    />
  );
}
