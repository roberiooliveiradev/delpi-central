import type { DataTableColumn } from "@delpi/plugin-ui/index";

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
      render: (row) => (
        <CommercialStatusBadge
          label={row.status_label || row.status_code || "—"}
          variant={statusBadgeVariant(row.status_category)}
        />
      ),
    },
    { key: "stage", header: "Etapa", render: (row) => row.stage || "—" },
    {
      key: "date",
      header: "Data",
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
  const baseColumns = buildCommercialProposalColumns({
    basePath,
    detailSearch,
    hideCustomerColumn,
    showOpenProposal,
  });
  const columns = withColumnHelp(baseColumns, PROPOSALS_DOCUMENTS_COLUMN_HELP);

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
      rowClickRole="button"
    />
  );
}
