/** Accessible monthly-averages table (PROC-0076).

Tabular alternative to the chart — every period row is rendered,
including explicit no-data and fx-missing coverage states.
*/

import { useEffect, useMemo, useState } from "react";

import {
  SuppliesCompactPagination,
  SuppliesDataTable,
  SuppliesSectionCard,
  SuppliesStateBanner,
  spDataTableClassNames,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import {
  getMarketIntelligenceMonthlyAverages,
  type MarketMonthlyAverageRow,
  type MarketQueryParams,
} from "./api";
import {
  mapMarketIntelligenceError,
  MARKET_INTELLIGENCE_CONTENT,
} from "./content";

const PAGE_SIZE = 12;

type MarketIntelligenceMonthlyTableProps = {
  params: MarketQueryParams;
  showNativeAverage: boolean;
  enabled: boolean;
};

function formatDecimal(raw: string | null): string {
  if (raw === null) return "—";
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) return "—";
  return parsed.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

function coverageLabel(coverage: string): string {
  return (
    MARKET_INTELLIGENCE_CONTENT.table.coverageLabels[coverage] ?? coverage
  );
}

export function MarketIntelligenceMonthlyTable({
  params,
  showNativeAverage,
  enabled,
}: MarketIntelligenceMonthlyTableProps) {
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<MarketMonthlyAverageRow[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [dataStatus, setDataStatus] = useState<string>("ok");
  const [partialReason, setPartialReason] = useState<string | null>(null);

  // Reset pagination when the data window changes.
  useEffect(() => setPage(1), [params]);

  useEffect(() => {
    if (!enabled || !params.instrument) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getMarketIntelligenceMonthlyAverages(
      { ...params, page, page_size: PAGE_SIZE },
      controller.signal,
    )
      .then((payload) => {
        setRows(payload.items);
        setTotal(payload.page_info.total_items);
        setTotalPages(payload.page_info.total_pages);
        setDataStatus(payload.meta.data_status);
        setPartialReason(payload.meta.partial_reason);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setRows([]);
        setTotal(0);
        setError(mapMarketIntelligenceError(err));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [enabled, params, page]);

  const columns = useMemo((): DataTableColumn<MarketMonthlyAverageRow>[] => {
    const numeric = {
      align: "right" as const,
      className: spDataTableClassNames.colNumeric,
    };
    const base: DataTableColumn<MarketMonthlyAverageRow>[] = [
      {
        key: "period",
        header: MARKET_INTELLIGENCE_CONTENT.table.periodColumn,
        render: (row) => row.period,
      },
      {
        key: "average",
        header: MARKET_INTELLIGENCE_CONTENT.table.averageColumn,
        render: (row) => formatDecimal(row.average),
        ...numeric,
      },
    ];
    if (showNativeAverage) {
      base.push({
        key: "native_average",
        header: MARKET_INTELLIGENCE_CONTENT.table.nativeAverageColumn,
        render: (row) => formatDecimal(row.native_average),
        ...numeric,
      });
      base.push({
        key: "fx_rate",
        header: MARKET_INTELLIGENCE_CONTENT.table.fxRateColumn,
        render: (row) => formatDecimal(row.fx_rate),
        ...numeric,
      });
    }
    base.push(
      {
        key: "observation_count",
        header: MARKET_INTELLIGENCE_CONTENT.table.observationsColumn,
        render: (row) => String(row.observation_count),
        ...numeric,
      },
      {
        key: "coverage",
        header: MARKET_INTELLIGENCE_CONTENT.table.coverageColumn,
        render: (row) => coverageLabel(row.coverage),
      },
    );
    return base;
  }, [showNativeAverage]);

  const showPartialNote =
    !loading && !error && (dataStatus === "partial" || partialReason);

  return (
    <SuppliesSectionCard
      title={MARKET_INTELLIGENCE_CONTENT.table.sectionTitle}
      hint={SP_HELP.marketIntelligenceMonthlyTable}
    >
      {error ? (
        <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
      ) : null}
      {showPartialNote ? (
        <SuppliesStateBanner>
          {partialReason?.startsWith("fx_missing")
            ? MARKET_INTELLIGENCE_CONTENT.states.fxMissingNote
            : MARKET_INTELLIGENCE_CONTENT.states.partialNote}
        </SuppliesStateBanner>
      ) : null}
      <div
        className="sp-list-table-region"
        role="region"
        aria-label={MARKET_INTELLIGENCE_CONTENT.table.sectionTitle}
        tabIndex={0}
      >
        <SuppliesDataTable
          layout="section"
          columns={columns}
          rows={rows}
          rowKey={(row) => row.period}
          loading={loading}
        />
      </div>
      <SuppliesCompactPagination
        page={page}
        pageSize={PAGE_SIZE}
        total={total}
        totalPages={Math.max(1, totalPages)}
        disabled={loading}
        onPageChange={setPage}
      />
    </SuppliesSectionCard>
  );
}
