type LoadingActivityCardVariant = "compact" | "panel";
type LoadingActivityCardTone = "neutral" | "info";

type LoadingActivityCardProps = {
  title: string;
  description?: string;
  variant?: LoadingActivityCardVariant;
  tone?: LoadingActivityCardTone;
  sticky?: boolean;
  progressPercent?: number;
};

export function LoadingActivityCard({
  title,
  description,
  variant = "panel",
  tone = "info",
  sticky = variant === "compact",
  progressPercent,
}: LoadingActivityCardProps) {
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
        "dc-loading-activity",
        `dc-loading-activity--${variant}`,
        `dc-loading-activity--${tone}`,
        sticky ? "dc-loading-activity--sticky" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="status"
      aria-live="polite"
    >
      <div className="dc-loading-activity__spinner" aria-hidden="true" />
      <div className="dc-loading-activity__content">
        <div>
          <strong className="dc-loading-activity__title">{title}</strong>
          {description ? (
            <p className="dc-loading-activity__description">{description}</p>
          ) : null}
        </div>
        <div className="dc-loading-activity__progress-wrap">
          {remainingPercent !== null ? (
            <span className="dc-loading-activity__progress-label">
              Faltam {remainingPercent}%
            </span>
          ) : null}
          <div
            className="dc-loading-activity__progress"
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
              className={`dc-loading-activity__progress-indicator${
                clampedProgress !== null
                  ? " dc-loading-activity__progress-indicator--determinate"
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
