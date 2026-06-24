import type { ReactNode } from "react";

type InfoCardVariant = "info" | "success" | "warning" | "neutral";

type InfoCardProps = {
  variant?: InfoCardVariant;
  icon?: ReactNode;
  title?: string;
  children: ReactNode;
};

export function InfoCard({
  variant = "neutral",
  icon,
  title,
  children,
}: InfoCardProps) {
  return (
    <article
      className={`ds-card ds-info-card ds-info-card--${variant}`}
      role={variant === "warning" ? "alert" : "status"}
    >
      {icon ? (
        <div className="ds-info-card__icon" aria-hidden="true">
          {icon}
        </div>
      ) : null}
      <div className="ds-info-card__body">
        {title ? <strong className="ds-info-card__title">{title}</strong> : null}
        <div className="ds-info-card__content">{children}</div>
      </div>
    </article>
  );
}
