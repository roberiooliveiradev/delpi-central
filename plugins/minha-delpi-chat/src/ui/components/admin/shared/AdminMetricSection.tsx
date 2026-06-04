import type { ReactNode } from "react";

type AdminMetricSectionProps = {
  id?: string;
  domain?: string;
  title: string;
  description?: string;
  isLoading?: boolean;
  loadingMessage?: string;
  isEmpty?: boolean;
  emptyMessage?: string;
  children?: ReactNode;
  className?: string;
};

export function AdminMetricSection({
  id,
  domain,
  title,
  description,
  isLoading = false,
  loadingMessage = "Carregando métricas...",
  isEmpty = false,
  emptyMessage = "Não foi possível carregar os dados.",
  children,
  className,
}: AdminMetricSectionProps) {
  const sectionClass = ["mdc-admin-metric-section", className].filter(Boolean).join(" ");

  return (
    <section className={sectionClass} aria-labelledby={id}>
      <header className="mdc-admin-metric-section__header">
        {domain ? <p className="mdc-chat-eyebrow">{domain}</p> : null}
        <h3 id={id}>{title}</h3>
        {description ? <p>{description}</p> : null}
      </header>

      {isLoading ? <p className="mdc-chat-muted">{loadingMessage}</p> : null}

      {!isLoading && isEmpty ? <p className="mdc-chat-muted">{emptyMessage}</p> : null}

      {!isLoading && !isEmpty && children ? (
        <div className="mdc-admin-metric-section__body">{children}</div>
      ) : null}
    </section>
  );
}
