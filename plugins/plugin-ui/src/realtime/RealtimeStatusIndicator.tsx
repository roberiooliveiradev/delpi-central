import type { RealtimeConnectionStatus } from "./realtimeSocket";

const DEFAULT_LABELS: Partial<Record<RealtimeConnectionStatus, string>> = {
  open: "Ao vivo",
  connecting: "Reconectando…",
  reconnecting: "Reconectando…",
  unavailable: "Atualização automática indisponível",
};

export type RealtimeStatusIndicatorProps = {
  status: RealtimeConnectionStatus;
  labels?: Partial<Record<RealtimeConnectionStatus, string>>;
  compact?: boolean;
};

export function RealtimeStatusIndicator({
  status,
  labels,
  compact = false,
}: RealtimeStatusIndicatorProps) {
  const text = (labels ?? DEFAULT_LABELS)[status] ?? DEFAULT_LABELS[status];
  if (!text || status === "idle" || status === "closed") return null;
  const className = [
    "delpi-ui-realtime-status",
    compact ? "delpi-ui-realtime-status--compact" : "",
    `delpi-ui-realtime-status--${status}`,
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <span className={className} role="status" aria-live="polite">
      {text}
    </span>
  );
}
