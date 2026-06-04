import type { ReactNode } from "react";

type AdminKpiCardProps = {
  title: string;
  value: ReactNode;
  hint?: string;
  wide?: boolean;
  children?: ReactNode;
  onClick?: () => void;
  active?: boolean;
  disabled?: boolean;
};

export function AdminKpiCard({
  title,
  value,
  hint,
  wide = false,
  children,
  onClick,
  active = false,
  disabled = false,
}: AdminKpiCardProps) {
  const className = [
    wide ? "mdc-admin-kpi-card mdc-admin-kpi-card--wide" : "mdc-admin-kpi-card",
    active ? "is-active" : "",
    onClick ? "is-clickable" : "",
  ]
    .filter(Boolean)
    .join(" ");

  if (onClick) {
    return (
      <article className={className}>
        <button
          type="button"
          className="mdc-admin-kpi-card__hit"
          disabled={disabled}
          onClick={onClick}
        >
          <h3>{title}</h3>
          <strong>{value}</strong>
          {hint ? <p>{hint}</p> : null}
          {children}
        </button>
      </article>
    );
  }

  return (
    <article className={className}>
      <h3>{title}</h3>
      <strong>{value}</strong>
      {hint ? <p>{hint}</p> : null}
      {children}
    </article>
  );
}

export function AdminKpiGrid({ children }: { children: ReactNode }) {
  return <div className="mdc-admin-kpi-grid">{children}</div>;
}
