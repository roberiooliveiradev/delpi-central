import type { DeliveryMapOpProgress } from "../types";

type DeliveryMapOpProgressBarProps = {
  progress: DeliveryMapOpProgress | null | undefined;
  ariaLabel: (progress: DeliveryMapOpProgress) => string;
};

function progressTone(progress: DeliveryMapOpProgress): "low" | "mid" | "high" | "complete" | "running" {
  if (progress.in_progress > 0 && progress.percent < 100) return "running";
  if (progress.percent >= 100) return "complete";
  if (progress.percent >= 67) return "high";
  if (progress.percent >= 34) return "mid";
  return "low";
}

export function DeliveryMapOpProgressBar({ progress, ariaLabel }: DeliveryMapOpProgressBarProps) {
  if (!progress || progress.total <= 0) return null;

  const tone = progressTone(progress);
  const width = Math.max(progress.percent > 0 ? 8 : 0, progress.percent);

  return (
    <span
      className="ppc-delivery-map__op-progress"
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={progress.percent}
      aria-label={ariaLabel(progress)}
      title={ariaLabel(progress)}
    >
      <span className="ppc-delivery-map__op-progress-track">
        <span
          className={`ppc-delivery-map__op-progress-fill ppc-delivery-map__op-progress-fill--${tone}`}
          style={{ width: `${width}%` }}
        />
      </span>
      {progress.percent > 0 ? (
        <span className="ppc-delivery-map__op-progress-pct" aria-hidden="true">
          {progress.percent}%
        </span>
      ) : null}
    </span>
  );
}
