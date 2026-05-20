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
        "dq-loading-activity",
        `dq-loading-activity--${variant}`,
        `dq-loading-activity--${tone}`,
        sticky ? "dq-loading-activity--sticky" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="status"
      aria-live="polite"
    >
      <div className="dq-loading-activity__spinner" aria-hidden="true" />
      <div className="dq-loading-activity__content">
        <div className="dq-loading-activity__copy">
          <strong className="dq-loading-activity__title">{title}</strong>
          {description ? (
            <p className="dq-loading-activity__description">{description}</p>
          ) : null}
        </div>
        <div className="dq-loading-activity__progress" aria-hidden="true">
          <div className="dq-loading-activity__progress-indicator" />
        </div>
      </div>
    </div>
  );
}
