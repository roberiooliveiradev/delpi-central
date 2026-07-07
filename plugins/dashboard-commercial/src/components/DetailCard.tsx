import type { ReactNode } from "react";

import { HelpTooltip } from "@delpi/plugin-ui";

type DetailCardProps = {
  title: string;
  titleHint?: string;
  hint?: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  headerActions?: ReactNode;
};

export function DetailCard({
  title,
  titleHint,
  hint,
  icon,
  children,
  className,
  headerActions,
}: DetailCardProps) {
  const cardClass = ["dc-card", "dc-detail-card", className]
    .filter(Boolean)
    .join(" ");

  return (
    <section className={cardClass}>
      <header className="dc-detail-card__header">
        {icon ? <div className="dc-detail-card__icon">{icon}</div> : null}
        <div className="dc-detail-card__heading">
          <h2 className="dc-detail-card__title">
            {title}
            {titleHint ? (
              <HelpTooltip
                content={titleHint}
                ariaLabel={`Ajuda: ${title}`}
                className="dc-detail-card__title-help"
              />
            ) : null}
          </h2>
          {hint ? <p className="dc-detail-card__hint">{hint}</p> : null}
        </div>
        {headerActions ? (
          <div className="dc-detail-card__actions dc-no-print">{headerActions}</div>
        ) : null}
      </header>
      <div className="dc-detail-card__body">{children}</div>
    </section>
  );
}
