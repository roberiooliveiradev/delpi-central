type LoadingActivityInlineVariant = "compact" | "panel";
type LoadingActivityInlineTone = "neutral" | "info";

type LoadingActivityInlineProps = {
  title: string;
  description?: string;
  variant?: LoadingActivityInlineVariant;
  tone?: LoadingActivityInlineTone;
  sticky?: boolean;
};

export function LoadingActivityInline({
  title,
  description,
  variant = "panel",
  tone = "neutral",
  sticky = variant === "compact",
}: LoadingActivityInlineProps) {
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

        <div
          className="si-loading-activity-inline__progress"
          aria-hidden="true"
        >
          <div className="si-loading-activity-inline__progress-indicator" />
        </div>
      </div>
    </div>
  );
}