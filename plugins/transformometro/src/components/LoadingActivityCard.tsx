type LoadingActivityCardProps = {
  title: string;
  description?: string;
  variant?: "compact" | "panel";
  sticky?: boolean;
};

export function LoadingActivityCard({
  title,
  description,
  variant = "panel",
  sticky = variant === "compact",
}: LoadingActivityCardProps) {
  return (
    <div
      className={[
        "ds-loading-activity",
        `ds-loading-activity--${variant}`,
        "ds-loading-activity--info",
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
