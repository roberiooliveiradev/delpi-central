import "./LoadingActivityInline.css";

type LoadingActivityInlineVariant = "compact" | "panel";
type LoadingActivityInlineTone = "neutral" | "info";

type LoadingActivityInlineProps = {
  title: string;
  description?: string;
  variant?: LoadingActivityInlineVariant;
  tone?: LoadingActivityInlineTone;
  sticky?: boolean;
  progressPercent?: number;
};

export function LoadingActivityInline({
  title,
  description,
  variant = "panel",
  tone = "neutral",
  sticky = variant === "compact",
  progressPercent,
}: LoadingActivityInlineProps) {
  const hasProgress =
    typeof progressPercent === "number" && Number.isFinite(progressPercent);
  const clampedProgress = hasProgress
    ? Math.min(100, Math.max(0, Math.round(progressPercent)))
    : null;
  const remainingPercent =
    clampedProgress !== null ? Math.max(0, 100 - clampedProgress) : null;
  return (
    <div
      className={[
        "si-loading-activity-inline",
        `si-loading-activity-inline--${variant}`,
        `si-loading-activity-inline--${tone}`,
        sticky ? "si-loading-activity-inline--sticky" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="status"
      aria-live="polite"
    >
      <div
        className="si-loading-activity-inline__spinner"
        aria-hidden="true"
      />

      <div className="si-loading-activity-inline__content">
        <div className="si-loading-activity-inline__copy">
          <strong className="si-loading-activity-inline__title">{title}</strong>

          {description ? (
            <p className="si-loading-activity-inline__description">
              {description}
            </p>
          ) : null}
        </div>

        <div className="si-loading-activity-inline__progress-wrap">
          {remainingPercent !== null ? (
            <span className="si-loading-activity-inline__progress-label">
              Faltam {remainingPercent}%
            </span>
          ) : null}

          <div
            className="si-loading-activity-inline__progress"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={clampedProgress ?? undefined}
            aria-label={
              remainingPercent !== null
                ? `Carregamento: faltam ${remainingPercent} por cento`
                : "Carregamento em andamento"
            }
          >
            <div
              className={`si-loading-activity-inline__progress-indicator${
                clampedProgress !== null
                  ? " si-loading-activity-inline__progress-indicator--determinate"
                  : ""
              }`}
              style={
                clampedProgress !== null
                  ? { width: `${clampedProgress}%` }
                  : undefined
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
}