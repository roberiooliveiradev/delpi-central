import { useMemo } from "react";

import {
  CommercialDataTable,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialSectionCard,
  type DataTableColumn,
} from "../../app/commercialUi";
import { PORTFOLIO_COVERAGE_CONTENT } from "../../content/portfolioCoverageContent";
import { CM_HELP } from "../../content/helpTooltips";
import type { UncoveredCustomerGapItem } from "../../types/portfolio";
import { customerKey } from "../../shared/format";
import { formatCompactOpenValue } from "../../utils/portfolioLoad";

type UncoveredCustomersPanelProps = {
  items: UncoveredCustomerGapItem[];
  uncoveredCount: number;
  available: boolean;
  loading: boolean;
};

export function UncoveredCustomersPanel({
  items,
  uncoveredCount,
  available,
  loading,
}: UncoveredCustomersPanelProps) {
  const columns = useMemo<DataTableColumn<UncoveredCustomerGapItem>[]>(
    () => [
      {
        key: "code",
        header: PORTFOLIO_COVERAGE_CONTENT.colCustomerCode,
        headerHint: CM_HELP.sellerPortfolios.colCustomerCode,
        render: (row) => `${row.customer_code}/${row.customer_store}`,
      },
      {
        key: "name",
        header: PORTFOLIO_COVERAGE_CONTENT.colCustomerName,
        headerHint: CM_HELP.sellerPortfolios.colCustomerName,
        render: (row) => row.customer_name?.trim() || "—",
      },
      {
        key: "open_value",
        header: PORTFOLIO_COVERAGE_CONTENT.colOpenValue,
        headerHint: CM_HELP.sellerPortfolios.colUncoveredOpenValue,
        render: (row) => formatCompactOpenValue(row.open_value),
      },
    ],
    [],
  );

  return (
    <CommercialSectionCard
      title={PORTFOLIO_COVERAGE_CONTENT.filterUncoveredPanelTitle}
      subtitle={PORTFOLIO_COVERAGE_CONTENT.filterUncoveredPanelSubtitle}
      hint={CM_HELP.sellerPortfolios.filterUncovered}
    >
      {loading ? (
        <CommercialLoadingCard title="Carregando cobertura…" variant="panel" />
      ) : !available ? (
        <CommercialEmptyState
          title={PORTFOLIO_COVERAGE_CONTENT.filterUncovered}
          message={PORTFOLIO_COVERAGE_CONTENT.filterUncoveredUnavailable}
        />
      ) : items.length === 0 ? (
        <CommercialEmptyState
          title={PORTFOLIO_COVERAGE_CONTENT.filterUncovered}
          message={PORTFOLIO_COVERAGE_CONTENT.filterUncoveredEmpty}
        />
      ) : (
        <>
          <p className="cm-section-subtitle">
            {uncoveredCount.toLocaleString("pt-BR")} cliente(s) sem cobertura
            {items.length < uncoveredCount
              ? ` (exibindo top ${items.length.toLocaleString("pt-BR")} por valor aberto)`
              : ""}
          </p>
          <CommercialDataTable
            rows={items}
            columns={columns}
            rowKey={(row, index) =>
              customerKey(row.customer_code, row.customer_store) || `gap-${index}`
            }
            layout="embedded"
          />
        </>
      )}
    </CommercialSectionCard>
  );
}
