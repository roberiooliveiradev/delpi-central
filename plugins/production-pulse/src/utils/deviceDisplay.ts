import type { DeviceListItem, DeviceStatus, DeviceSummary } from "../types/device";

const ROLE_LABELS: Record<string, string> = {
  pulse_counter: "Contador",
  process_gauge: "Sensor",
  telemetry: "Telemetria",
};

const ANCHOR_TYPE_LABELS: Record<string, string> = {
  work_center: "Posto",
  machine: "Máquina",
  equipment: "Equipamento",
  area: "Área",
  standalone: "Avulso",
};

const METRIC_LABELS: Record<string, { label: string; unit?: string }> = {
  counter: { label: "Golpes", unit: "gol" },
  rpm: { label: "Rotação", unit: "rpm" },
  temperature_c: { label: "Temperatura", unit: "°C" },
};

export function roleLabel(roleKey: string): string {
  return ROLE_LABELS[roleKey] ?? roleKey;
}

export function anchorTypeLabel(anchorType: string): string {
  return ANCHOR_TYPE_LABELS[anchorType] ?? anchorType;
}

export function formatRelativeTime(iso: string | null | undefined, now = Date.now()): string {
  if (!iso) return "—";
  const timestamp = Date.parse(iso);
  if (Number.isNaN(timestamp)) return "—";
  const diffSeconds = Math.max(0, Math.floor((now - timestamp) / 1000));
  if (diffSeconds < 60) return `${diffSeconds} s`;
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) return `${diffMinutes} min`;
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 48) return `${diffHours} h`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} d`;
}

function primaryMetricKey(device: DeviceListItem): string | null {
  const metrics = device.lastMetrics ?? {};
  const keys = Object.keys(metrics);
  if (keys.length === 0) return null;
  if (keys.includes("counter")) return "counter";
  if (keys.includes("rpm")) return "rpm";
  return keys[0] ?? null;
}

export function formatPrimaryMetric(device: DeviceListItem): string {
  const key = primaryMetricKey(device);
  if (!key) return "—";
  const raw = device.lastMetrics[key];
  if (raw === null || raw === undefined || raw === "") return "—";
  const meta = METRIC_LABELS[key];
  const formatted =
    typeof raw === "number"
      ? new Intl.NumberFormat("pt-BR").format(raw)
      : String(raw);
  if (!meta?.unit) return formatted;
  return `${formatted} ${meta.unit}`;
}

export function formatCounterPeriodDelta(
  device: DeviceListItem,
  period: "day" | "shift",
): string | null {
  if (device.roleKey !== "pulse_counter") return null;
  const value = device.periodDeltas?.[period]?.counter;
  if (value === null || value === undefined) return null;
  return `+${new Intl.NumberFormat("pt-BR").format(value)}`;
}

export function formatCounterDeltaKpi(
  counterDelta: DeviceSummary["counterDelta"],
  period: "day" | "shift",
): string {
  const value = counterDelta?.[period]?.counter ?? 0;
  return new Intl.NumberFormat("pt-BR").format(value);
}

export function placementLabel(device: DeviceListItem): string {
  if (!device.binding) return "—";
  return device.binding.placementLabel || "—";
}

export function statusLabel(status: DeviceStatus): string {
  if (status === "online") return "Online";
  if (status === "offline") return "Offline";
  if (status === "disabled") return "Desativado";
  return "Sem amarração";
}

export type ViewportBucket = "mobile" | "tablet" | "desktop";

export function resolveViewportBucket(width: number): ViewportBucket {
  if (width <= 768) return "mobile";
  if (width <= 1100) return "tablet";
  return "desktop";
}
