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
        "ds-loading-activity",
        `ds-loading-activity--${variant}`,
        `ds-loading-activity--${tone}`,
        sticky ? "ds-loading-activity--sticky" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="status"
      aria-live="polite"
    >
      <div className="ds-loading-activity__spinner" aria-hidden="true" />
      <div className="ds-loading-activity__content">
        <div className="ds-loading-activity__copy">
          <strong className="ds-loading-activity__title">{title}</strong>
          {description ? (
            <p className="ds-loading-activity__description">{description}</p>
          ) : null}
        </div>
        <div className="ds-loading-activity__progress" aria-hidden="true">
          <div className="ds-loading-activity__progress-indicator" />
        </div>
      </div>
    </div>
  );
}
