import type { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  badge?: ReactNode;
  actions?: ReactNode;
};

export function PageHeader({
  eyebrow,
  title,
  description,
  badge,
  actions,
}: PageHeaderProps) {
  return (
    <header className="si-page-header">
      <div className="si-page-header__content">
        {eyebrow ? <p className="si-page-header__eyebrow">{eyebrow}</p> : null}

        <div className="si-page-header__title-row">
          <h1 className="si-page-header__title">{title}</h1>
          {badge ? <div className="si-page-header__badge">{badge}</div> : null}
        </div>

        {description ? (
          <p className="si-page-header__description">{description}</p>
        ) : null}
      </div>

      {actions ? <div className="si-page-header__actions">{actions}</div> : null}
    </header>
  );
}