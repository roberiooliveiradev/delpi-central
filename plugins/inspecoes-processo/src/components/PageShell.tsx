import type { ReactNode } from "react";

type PageShellProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function PageShell({ title, description, actions, children }: PageShellProps) {
  return (
    <section className="ip-page-shell">
      <div className="ip-page-shell__header">
        <div>
          <h2 className="ip-page-shell__title">{title}</h2>
          {description ? (
            <p className="ip-page-shell__description">{description}</p>
          ) : null}
        </div>
        {actions ? <div className="ip-page-shell__actions">{actions}</div> : null}
      </div>
      <div className="ip-page-shell__body">{children}</div>
    </section>
  );
}
