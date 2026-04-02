import type { PropsWithChildren, ReactNode } from "react";

type CardProps = PropsWithChildren<{
  title?: string;
  description?: string;
  headerRight?: ReactNode;
  className?: string;
}>;

export function Card({
  title,
  description,
  headerRight,
  className = "",
  children,
}: CardProps) {
  return (
    <section className={`si-card ${className}`.trim()}>
      {(title || description || headerRight) && (
        <header className="si-card__header">
          <div className="si-card__header-content">
            {title ? <h3 className="si-card__title">{title}</h3> : null}
            {description ? (
              <p className="si-card__description">{description}</p>
            ) : null}
          </div>

          {headerRight ? (
            <div className="si-card__header-right">{headerRight}</div>
          ) : null}
        </header>
      )}

      <div className="si-card__body">{children}</div>
    </section>
  );
}