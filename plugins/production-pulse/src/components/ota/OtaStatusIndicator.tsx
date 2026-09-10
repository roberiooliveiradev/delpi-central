import type { LucideIcon } from "lucide-react";

import { resolveOtaVisualState, type OtaVisualTone } from "../utils/otaVisualState";

type Density = "compact" | "comfortable";

type OtaStatusIndicatorProps = {
  status?: string | null;
  errorCode?: string | null;
  deviceOnline?: boolean | null;
  progressPercent?: number | null;
  bytesReceived?: number | null;
  bytesTotal?: number | null;
  density?: Density;
  className?: string;
  meta?: string | null;
  onActionClick?: () => void;
  actionLabel?: string;
};

const TONE_CLASS: Record<OtaVisualTone, string> = {
  muted: "pp-ota-state--muted",
  info: "pp-ota-state--info",
  accent: "pp-ota-state--accent",
  success: "pp-ota-state--success",
  warning: "pp-ota-state--warning",
  danger: "pp-ota-state--danger",
};

export function OtaStatusIndicator({
  status,
  errorCode,
  deviceOnline,
  progressPercent,
  bytesReceived,
  bytesTotal,
  density = "compact",
  className,
  meta,
  onActionClick,
  actionLabel,
}: OtaStatusIndicatorProps) {
  const visual = resolveOtaVisualState({
    status,
    errorCode,
    deviceOnline,
    progressPercent,
    bytesReceived,
    bytesTotal,
  });
  const Icon = visual.icon as LucideIcon;
  const spin = visual.progressMode === "indeterminate" || status === "applying";

  return (
    <div
      className={[
        "pp-ota-state",
        `pp-ota-state--${density}`,
        TONE_CLASS[visual.tone],
        className || "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="status"
      aria-label={visual.label}
    >
      <Icon
        className={["pp-ota-state__icon", spin ? "pp-ota-state__icon--spin" : ""]
          .filter(Boolean)
          .join(" ")}
        aria-hidden
        size={density === "compact" ? 14 : 18}
      />
      <div className="pp-ota-state__text">
        <span className="pp-ota-state__label">{visual.label}</span>
        {meta ? <span className="pp-ota-state__meta">{meta}</span> : null}
        {density !== "compact" && visual.description && visual.phase === "failed" ? (
          <span className="pp-ota-state__meta">{visual.description}</span>
        ) : null}
      </div>
      {onActionClick && actionLabel ? (
        <button type="button" className="pp-ota-state__action" onClick={onActionClick}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
