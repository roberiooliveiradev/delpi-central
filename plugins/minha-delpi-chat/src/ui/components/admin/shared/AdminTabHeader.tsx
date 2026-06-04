import type { ReactNode } from "react";

type AdminTabHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  summary?: ReactNode;
  className?: string;
};

export function AdminTabHeader({
  eyebrow,
  title,
  description,
  actions,
  summary,
  className,
}: AdminTabHeaderProps) {
  const rootClass = ["mdc-admin-tab-header", className].filter(Boolean).join(" ");

  return (
    <header className={rootClass}>
      <div className="mdc-admin-page-header">
        {eyebrow ? <p className="mdc-chat-eyebrow">{eyebrow}</p> : null}
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {summary}
      {actions ? <div className="mdc-admin-tab-header__actions">{actions}</div> : null}
    </header>
  );
}
