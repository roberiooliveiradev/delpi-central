type LoadingActivityCardVariant = "compact" | "panel";
type LoadingActivityCardTone = "neutral" | "info";

type LoadingActivityCardProps = {
  title: string;
  description?: string;
  variant?: LoadingActivityCardVariant;
  tone?: LoadingActivityCardTone;
  sticky?: boolean;
};

export function LoadingActivityCard({
  title,
  description,
  variant = "panel",
  tone = "info",
  sticky = variant === "compact",
}: LoadingActivityCardProps) {
  return (
    <div
      className={[
        "lmps-loading-activity",
        `lmps-loading-activity--${variant}`,
        `lmps-loading-activity--${tone}`,
        sticky ? "lmps-loading-activity--sticky" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="status"
      aria-live="polite"
    >
      <div className="lmps-loading-activity__spinner" aria-hidden="true" />
      <div className="lmps-loading-activity__content">
        <div className="lmps-loading-activity__copy">
          <strong className="lmps-loading-activity__title">{title}</strong>
          {description ? (
            <p className="lmps-loading-activity__description">{description}</p>
          ) : null}
        </div>
        <div className="lmps-loading-activity__progress" aria-hidden="true">
          <div className="lmps-loading-activity__progress-indicator" />
        </div>
      </div>
    </div>
  );
}
