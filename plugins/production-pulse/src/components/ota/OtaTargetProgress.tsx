import { PpOtaProgressBar } from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";
import { formatRelativeTime } from "../../utils/deviceDisplay";
import { resolveOtaVisualState } from "../../utils/otaVisualState";
import { OtaStatusIndicator } from "./OtaStatusIndicator";

type OtaTargetProgressProps = {
  status?: string | null;
  errorCode?: string | null;
  deviceOnline?: boolean | null;
  progressPercent?: number | null;
  bytesReceived?: number | null;
  bytesTotal?: number | null;
  updatedAt?: string | null;
  showTrackerMeta?: boolean;
  className?: string;
};

export function OtaTargetProgress({
  status,
  errorCode,
  deviceOnline,
  progressPercent,
  bytesReceived,
  bytesTotal,
  updatedAt,
  showTrackerMeta = true,
  className,
}: OtaTargetProgressProps) {
  const visual = resolveOtaVisualState({
    status,
    errorCode,
    deviceOnline,
    progressPercent,
    bytesReceived,
    bytesTotal,
  });

  const lastActivity =
    updatedAt && showTrackerMeta
      ? `${PP_HELP.ota.lastActivity} ${formatRelativeTime(updatedAt)}`
      : null;

  return (
    <div className={["pp-ota-target-progress", className || ""].filter(Boolean).join(" ")}>
      <OtaStatusIndicator
        status={status}
        errorCode={errorCode}
        deviceOnline={deviceOnline}
        progressPercent={progressPercent}
        bytesReceived={bytesReceived}
        bytesTotal={bytesTotal}
        density="comfortable"
        meta={lastActivity}
      />
      {visual.progressMode === "determinate" && visual.progressPercent != null ? (
        <div className="pp-ota-target-progress__bar">
          <PpOtaProgressBar
            value={visual.progressPercent}
            ariaLabel={visual.label}
            label={visual.label}
          />
          {visual.bytesLabel ? (
            <span className="pp-ota-target-progress__bytes">{visual.bytesLabel}</span>
          ) : null}
        </div>
      ) : null}
      {visual.technicalCode ? (
        <p className="pp-ota-target-progress__code">
          {PP_HELP.ota.technicalCode}: {visual.technicalCode}
        </p>
      ) : null}
    </div>
  );
}
