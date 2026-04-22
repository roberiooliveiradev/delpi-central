type LoadingActivityBadgeTone = "neutral" | "info";

type LoadingActivityBadgeProps = {
  label?: string;
  tone?: LoadingActivityBadgeTone;
  showBar?: boolean;
};

export function LoadingActivityBadge({
  label = "Atualizando",
  tone = "neutral",
  showBar = false,
}: LoadingActivityBadgeProps) {
  return (
    <span
      className={`si-loading-activity-badge si-loading-activity-badge--${tone}`}
      role="status"
      aria-live="polite"
    >
      <span
        className="si-loading-activity-badge__spinner"
        aria-hidden="true"
      />

      <span className="si-loading-activity-badge__label">{label}</span>

      {showBar ? (
        <span
          className="si-loading-activity-badge__bar"
          aria-hidden="true"
        >
          <span className="si-loading-activity-badge__bar-indicator" />
        </span>
      ) : null}
    </span>
  );
}