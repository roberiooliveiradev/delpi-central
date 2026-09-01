import type { DeviceListItem } from "../types/device";
import type { DeviceReading } from "../types/detail";

const METRIC_LABELS: Record<string, { label: string; unit?: string }> = {
  counter: { label: "Golpes", unit: "gol" },
  rpm: { label: "Rotação", unit: "rpm" },
  temperature_c: { label: "Temperatura", unit: "°C" },
};

const SOURCE_LABELS: Record<string, string> = {
  poll: "Poll",
  manual: "Manual",
  command: "Comando",
};

const COMMAND_LABELS: Record<string, string> = {
  reset: "Reset",
  increment: "+1",
  decrement: "−1",
};

export function metricLabel(key: string): string {
  return METRIC_LABELS[key]?.label ?? key;
}

export function metricUnit(key: string): string | undefined {
  return METRIC_LABELS[key]?.unit;
}

export function primaryMetricKey(
  metrics: Record<string, number | string> | undefined,
  capabilities?: { metrics?: string[] },
): string | null {
  const keys = Object.keys(metrics ?? {});
  if (keys.length === 0 && capabilities?.metrics?.length) {
    return capabilities.metrics[0] ?? null;
  }
  if (keys.includes("counter")) return "counter";
  if (keys.includes("rpm")) return "rpm";
  return keys[0] ?? capabilities?.metrics?.[0] ?? null;
}

export function formatMetricValue(
  key: string,
  raw: number | string | null | undefined,
): string {
  if (raw === null || raw === undefined || raw === "") return "—";
  const formatted =
    typeof raw === "number"
      ? new Intl.NumberFormat("pt-BR").format(raw)
      : String(raw);
  const unit = metricUnit(key);
  return unit ? `${formatted} ${unit}` : formatted;
}

export function formatDeltaValue(
  key: string,
  raw: number | string | null | undefined,
): string {
  if (raw === null || raw === undefined || raw === "") return "—";
  const numeric = typeof raw === "number" ? raw : Number(raw);
  if (Number.isNaN(numeric)) return String(raw);
  const prefix = numeric > 0 ? "+" : "";
  const formatted = new Intl.NumberFormat("pt-BR").format(numeric);
  const unit = metricUnit(key);
  return unit ? `${prefix}${formatted} ${unit}` : `${prefix}${formatted}`;
}

export function formatPrimaryMetricFromDevice(device: DeviceListItem): string {
  const key = primaryMetricKey(device.lastMetrics, device.capabilities);
  if (!key) return "—";
  return formatMetricValue(key, device.lastMetrics[key]);
}

export function sourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source;
}

export function commandLabel(commandKey: string): string {
  return COMMAND_LABELS[commandKey] ?? commandKey;
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

export function formatDateOnly(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}

export function isoHoursAgo(hours: number): string {
  return new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
}

export type ChartPoint = {
  x: string;
  y: number;
  label: string;
};

export function readingsToChartPoints(
  readings: DeviceReading[],
  metricKey: string,
  mode: "value" | "delta",
): ChartPoint[] {
  const chronological = [...readings].reverse();
  return chronological
    .map((row) => {
      const raw =
        mode === "delta"
          ? row.deltaMetrics?.[metricKey]
          : row.metrics?.[metricKey];
      const numeric = typeof raw === "number" ? raw : Number(raw);
      if (Number.isNaN(numeric)) return null;
      return {
        x: row.recordedAt,
        y: numeric,
        label: formatDateTime(row.recordedAt),
      };
    })
    .filter((point): point is ChartPoint => point !== null);
}

export function driverLabel(driverKey: string): string {
  if (driverKey === "esp8266_counter_v1") return "ESP8266 contador";
  if (driverKey === "esp8266_gauge_v1") return "ESP8266 sensor";
  return driverKey;
}
