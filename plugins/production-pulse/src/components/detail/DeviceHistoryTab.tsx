import { useEffect, useMemo, useState } from "react";

import { fetchDeviceReadings } from "../../api/productionPulseApi";
import {
  PpActionButton,
  PpChartCard,
  PpPagination,
  PpSectionCard,
  PpSegmentToggle,
} from "../../app/productionPulseUi";
import { PpDataTable, type DataTableColumn } from "../data/dataTableUi";
import { PpFilterInputField, PpFiltersRow } from "../data/filtersUi";
import { SimpleLineChart } from "../charts/SimpleLineChart";
import type { DeviceListItem } from "../../types/device";
import type { DeviceReading } from "../../types/detail";
import { PP_HELP } from "../../content/helpTooltips";
import { useViewportBucket } from "../../hooks/useViewportBucket";
import {
  formatDateTime,
  formatDeltaValue,
  formatMetricValue,
  primaryMetricKey,
  readingsToChartPoints,
  sourceLabel,
} from "../../utils/detailDisplay";
import { ReadingCard } from "./ReadingCard";

const PAGE_SIZE = 20;

type DeviceHistoryTabProps = {
  device: DeviceListItem;
};

type ChartMode = "value" | "delta";

export function DeviceHistoryTab({ device }: DeviceHistoryTabProps) {
  const viewport = useViewportBucket();
  const isMobile = viewport === "mobile";
  const metricKey = primaryMetricKey(device.lastMetrics, device.capabilities);

  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [appliedFrom, setAppliedFrom] = useState<string | undefined>();
  const [appliedTo, setAppliedTo] = useState<string | undefined>();
  const [page, setPage] = useState(1);
  const [chartMode, setChartMode] = useState<ChartMode>("value");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [readings, setReadings] = useState<DeviceReading[]>([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    fetchDeviceReadings(device.id, {
      page,
      pageSize: PAGE_SIZE,
      from: appliedFrom,
      to: appliedTo,
      metric: metricKey ?? undefined,
      signal: controller.signal,
    })
      .then((payload) => {
        setReadings(payload.items);
        setTotal(payload.pagination.total);
        setLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar histórico.");
        setLoading(false);
      });
    return () => controller.abort();
  }, [appliedFrom, appliedTo, device.id, metricKey, page]);

  const chartPoints = useMemo(
    () => (metricKey ? readingsToChartPoints(readings, metricKey, chartMode) : []),
    [chartMode, metricKey, readings],
  );

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const columns = useMemo<DataTableColumn<DeviceReading>[]>(() => {
    const key = metricKey ?? "counter";
    return [
      {
        key: "recordedAt",
        header: "Data/hora",
        render: (row) => formatDateTime(row.recordedAt),
      },
      {
        key: "metric",
        header: key,
        render: (row) => formatMetricValue(key, row.metrics[key]),
      },
      {
        key: "delta",
        header: "Delta",
        headerHint: PP_HELP.detail.delta,
        render: (row) => formatDeltaValue(key, row.deltaMetrics?.[key]),
      },
      {
        key: "source",
        header: "Origem",
        render: (row) => sourceLabel(row.source),
      },
    ];
  }, [metricKey]);

  const applyFilters = () => {
    setPage(1);
    setAppliedFrom(fromDate ? new Date(`${fromDate}T00:00:00`).toISOString() : undefined);
    setAppliedTo(toDate ? new Date(`${toDate}T23:59:59`).toISOString() : undefined);
  };

  return (
    <div className="pp-detail-history">
      <PpFiltersRow>
        <PpFilterInputField
          id="pp-history-from"
          label="De"
          type="date"
          value={fromDate}
          onChange={setFromDate}
        />
        <PpFilterInputField
          id="pp-history-to"
          label="Até"
          type="date"
          value={toDate}
          onChange={setToDate}
        />
        <PpActionButton variant="ghost" onClick={applyFilters}>
          Aplicar
        </PpActionButton>
      </PpFiltersRow>

      <PpChartCard
        title={`Evolução — ${metricKey ?? "métrica"}`}
        titleHint={PP_HELP.detail.chartSeries}
        headerActions={
          <PpSegmentToggle
            ariaLabel="Modo do gráfico"
            value={chartMode}
            onChange={(value) => setChartMode(value as ChartMode)}
            options={[
              { value: "value", label: "Contador" },
              { value: "delta", label: "Delta" },
            ]}
          />
        }
      >
        <SimpleLineChart points={chartPoints} height={isMobile ? 180 : 240} />
      </PpChartCard>

      <PpSectionCard title="Leituras" hint={PP_HELP.detail.readingsTable}>
        {error ? <p className="pp-detail-error">{error}</p> : null}
        {isMobile ? (
          <div className="pp-reading-card-list">
            {readings.map((reading) => (
              <ReadingCard key={reading.id} reading={reading} metricKey={metricKey} />
            ))}
            {readings.length === 0 && !loading ? (
              <p className="pp-detail-muted">Nenhuma leitura encontrada.</p>
            ) : null}
          </div>
        ) : (
          <PpDataTable
            columns={columns}
            rows={readings}
            loading={loading}
            rowKey={(row) => String(row.id)}
            emptyMessage="Nenhuma leitura encontrada."
          />
        )}
        <PpPagination
          page={page}
          pageSize={PAGE_SIZE}
          total={total}
          totalPages={totalPages}
          onPageChange={setPage}
          hideWhenSinglePage
        />
      </PpSectionCard>
    </div>
  );
}
