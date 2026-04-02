type StatusVariant = "neutral" | "info" | "success" | "warning" | "danger";

type StatusBadgeProps = {
  label: string;
  variant?: StatusVariant;
};

export function StatusBadge({
  label,
  variant = "neutral",
}: StatusBadgeProps) {
  return (
    <span className={`si-status-badge si-status-badge--${variant}`}>
      {label}
    </span>
  );
}