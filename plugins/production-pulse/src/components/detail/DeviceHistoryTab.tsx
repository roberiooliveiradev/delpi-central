import { useEffect, useMemo, useState } from "react";

import { fetchDeviceReadings } from "../../api/productionPulseApi";
import {
  PpChartCard,
  PpDataTable,
  PpFilterInputField,
  PpFiltersRow,
  PpPagination,
  PpReadingsAreaChart,
  PpSectionCard,
  PpSegmentToggle,
  type DataTableColumn,
} from "../../app/productionPulseUi";
import type { DeviceListItem } from "../../types/device";
import type { DeviceReading } from "../../types/detail";
import { PP_HELP } from "../../content/helpTooltips";
import { useViewportBucket } from "../../hooks/useViewportBucket";
import { isMobileViewport } from "../../utils/viewportLayout";
import {
  formatDateTime,
  formatDeltaValue,
  formatMetricValue,
  isHardwareCounterReset,
  primaryMetricKey,
  readingsToChartPoints,
  sourceLabel,
} from "../../utils/detailDisplay";
import {
  HISTORY_RANGE_PRESET_OPTIONS,
  applyAdaptiveChartLabels,
  boundsForHistoryPreset,
  datetimeLocalToIso,
  downsampleChartPoints,
  formatChartTick,
  isoToDatetimeLocalValue,
  resolveChartTickGranularity,
  resolveDefaultHistoryPreset,
  resolveHistoryChartPageSize,
  resolveHistoryChartSampleIntervalMs,
  type HistoryRangePreset,
} from "../../utils/historyTimeRange";
import { ReadingHardwareResetBadge } from "./ReadingHardwareResetBadge";
import { ReadingCard } from "./ReadingCard";

const PAGE_SIZE = 20;
const FILTER_DEBOUNCE_MS = 350;

type DeviceHistoryTabProps = {
  device: DeviceListItem;
  refreshToken?: number;
};

type ChartMode = "value" | "delta";

function initialRange(pollIntervalMs: number) {
  const preset = resolveDefaultHistoryPreset(pollIntervalMs);
  const bounds = boundsForHistoryPreset(preset);
  return {
    preset,
    fromIso: bounds.fromIso,
    toIso: bounds.toIso,
    fromLocal: isoToDatetimeLocalValue(bounds.fromIso),
    toLocal: isoToDatetimeLocalValue(bounds.toIso),
  };
}

export function DeviceHistoryTab({ device, refreshToken = 0 }: DeviceHistoryTabProps) {
  const viewport = useViewportBucket();
  const isMobile = isMobileViewport(viewport);
  const metricKey = primaryMetricKey(device.lastMetrics, device.capabilities);
  const seed = useMemo(() => initialRange(device.pollIntervalMs), [device.id, device.pollIntervalMs]);

  const [preset, setPreset] = useState<HistoryRangePreset>(seed.preset);
  const [fromLocal, setFromLocal] = useState(seed.fromLocal);
  const [toLocal, setToLocal] = useState(seed.toLocal);
  const [appliedFrom, setAppliedFrom] = useState(seed.fromIso);
  const [appliedTo, setAppliedTo] = useState(seed.toIso);
  const [page, setPage] = useState(1);
  const [chartMode, setChartMode] = useState<ChartMode>("value");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [readings, setReadings] = useState<DeviceReading[]>([]);
  const [chartReadings, setChartReadings] = useState<DeviceReading[]>([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const next = initialRange(device.pollIntervalMs);
    setPreset(next.preset);
    setFromLocal(next.fromLocal);
    setToLocal(next.toLocal);
    setAppliedFrom(next.fromIso);
    setAppliedTo(next.toIso);
    setPage(1);
  }, [device.id, device.pollIntervalMs]);

  useEffect(() => {
    if (preset === "custom") return;
    const bounds = boundsForHistoryPreset(preset);
    setFromLocal(isoToDatetimeLocalValue(bounds.fromIso));
    setToLocal(isoToDatetimeLocalValue(bounds.toIso));
    setAppliedFrom(bounds.fromIso);
    setAppliedTo(bounds.toIso);
    setPage(1);
  }, [preset]);

  useEffect(() => {
    if (refreshToken === 0 || preset === "custom") return;
    const bounds = boundsForHistoryPreset(preset);
    setFromLocal(isoToDatetimeLocalValue(bounds.fromIso));
    setToLocal(isoToDatetimeLocalValue(bounds.toIso));
    setAppliedFrom(bounds.fromIso);
    setAppliedTo(bounds.toIso);
  }, [preset, refreshToken]);

  useEffect(() => {
    if (preset !== "custom") return;
    const handle = window.setTimeout(() => {
      const fromIso = datetimeLocalToIso(fromLocal);
      const toIso = datetimeLocalToIso(toLocal);
      setAppliedFrom(fromIso ?? "");
      setAppliedTo(toIso ?? "");
      setPage(1);
    }, FILTER_DEBOUNCE_MS);
    return () => window.clearTimeout(handle);
  }, [fromLocal, toLocal, preset]);

  useEffect(() => {
    const controller = new AbortController();
    const quiet = refreshToken > 0;
    if (!quiet) {
      setLoading(true);
    }
    setError(null);

    const from = appliedFrom || undefined;
    const to = appliedTo || undefined;
    const chartPageSize = resolveHistoryChartPageSize(from, to, device.pollIntervalMs);
    const sampleIntervalMs = resolveHistoryChartSampleIntervalMs(
      from,
      to,
      device.pollIntervalMs,
    );

    Promise.all([
      fetchDeviceReadings(device.id, {
        page,
        pageSize: PAGE_SIZE,
        from,
        to,
        metric: metricKey ?? undefined,
        signal: controller.signal,
      }),
      fetchDeviceReadings(device.id, {
        page: 1,
        pageSize: chartPageSize,
        from,
        to,
        metric: metricKey ?? undefined,
        sampleIntervalMs,
        signal: controller.signal,
      }),
    ])
      .then(([tablePayload, chartPayload]) => {
        setReadings(tablePayload.items);
        setTotal(tablePayload.pagination.total);
        setChartReadings(chartPayload.items);
        setLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar histórico.");
        setChartReadings([]);
        setLoading(false);
      });
    return () => controller.abort();
  }, [appliedFrom, appliedTo, device.id, device.pollIntervalMs, metricKey, page, refreshToken]);

  const chartPoints = useMemo(() => {
    if (!metricKey) return [];
    const granularity = resolveChartTickGranularity(appliedFrom, appliedTo, device.pollIntervalMs);
    const raw = readingsToChartPoints(chartReadings, metricKey, chartMode, (iso) =>
      formatChartTick(iso, granularity),
    );
    return applyAdaptiveChartLabels(downsampleChartPoints(raw), granularity);
  }, [appliedFrom, appliedTo, chartMode, chartReadings, device.pollIntervalMs, metricKey]);

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
        render: (row) => (
          <span className="pp-reading-delta-cell">
            {formatDeltaValue(key, row.deltaMetrics?.[key])}
            {isHardwareCounterReset(row) ? <ReadingHardwareResetBadge compact /> : null}
          </span>
        ),
      },
      {
        key: "source",
        header: "Origem",
        render: (row) => sourceLabel(row.source),
      },
    ];
  }, [metricKey]);

  const onFromChange = (value: string) => {
    setPreset("custom");
    setFromLocal(value);
  };

  const onToChange = (value: string) => {
    setPreset("custom");
    setToLocal(value);
  };

  return (
    <div className="pp-detail-history">
      <div className="pp-detail-history__toolbar">
        <PpSegmentToggle
          ariaLabel={PP_HELP.detail.historyRangePresets}
          value={preset}
          onChange={(value) => setPreset(value as HistoryRangePreset)}
          options={[
            ...HISTORY_RANGE_PRESET_OPTIONS.map((item) => ({
              value: item.value,
              label: item.label,
            })),
            { value: "custom", label: "Livre" },
          ]}
        />
        <PpFiltersRow className="pp-detail-history__filters">
          <PpFilterInputField
            id="pp-history-from"
            label="De"
            type="datetime-local"
            value={fromLocal}
            onChange={onFromChange}
          />
          <PpFilterInputField
            id="pp-history-to"
            label="Até"
            type="datetime-local"
            value={toLocal}
            onChange={onToChange}
          />
        </PpFiltersRow>
      </div>

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
        <PpReadingsAreaChart points={chartPoints} height={isMobile ? 200 : 280} variant="detail" />
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
