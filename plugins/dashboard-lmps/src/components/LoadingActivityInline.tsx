import "./LoadingActivityInline.css";

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
  tone = "info",
  sticky = variant === "compact",
}: LoadingActivityInlineProps) {
  return (
    <div
      className={[
        "lmps-loading-activity-inline",
        `lmps-loading-activity-inline--${variant}`,
        `lmps-loading-activity-inline--${tone}`,
        sticky ? "lmps-loading-activity-inline--sticky" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="status"
      aria-live="polite"
    >
      <div
        className="lmps-loading-activity-inline__spinner"
        aria-hidden="true"
      />

      <div className="lmps-loading-activity-inline__content">
        <div className="lmps-loading-activity-inline__copy">
          <strong className="lmps-loading-activity-inline__title">{title}</strong>

          {description ? (
            <p className="lmps-loading-activity-inline__description">
              {description}
            </p>
          ) : null}
        </div>

        <div
          className="lmps-loading-activity-inline__progress"
          aria-hidden="true"
        >
          <div className="lmps-loading-activity-inline__progress-indicator" />
        </div>
      </div>
    </div>
  );
}
