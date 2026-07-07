import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

export type DetailCardClassNames = {
  card: string;
  header: string;
  icon?: string;
  heading?: string;
  title: string;
  titleHelp?: string;
  description?: string;
  hint?: string;
  actions?: string;
  body?: string;
  wrapBody: boolean;
};

export type DetailCardLabels = {
  titleHelpAriaLabel: (title: string) => string;
};

export type DetailCardProps = {
  title: string;
  titleHint?: string;
  hint?: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  headerActions?: ReactNode;
  classNames: DetailCardClassNames;
  labels: DetailCardLabels;
};

export function detailCardProductionBemClasses(prefix: string): DetailCardClassNames {
  return {
    card: `${prefix}-card ${prefix}-detail-card`,
    header: `${prefix}-detail-card__header`,
    icon: `${prefix}-summary-card__icon`,
    title: `${prefix}-summary-card__title`,
    description: `${prefix}-summary-card__description`,
    wrapBody: false,
  };
}

export function detailCardRichBemClasses(prefix: string): DetailCardClassNames {
  return {
    card: `${prefix}-card ${prefix}-detail-card`,
    header: `${prefix}-detail-card__header`,
    icon: `${prefix}-detail-card__icon`,
    heading: `${prefix}-detail-card__heading`,
    title: `${prefix}-detail-card__title`,
    titleHelp: `${prefix}-detail-card__title-help`,
    hint: `${prefix}-detail-card__hint`,
    actions: `${prefix}-detail-card__actions ${prefix}-no-print`,
    body: `${prefix}-detail-card__body`,
    wrapBody: true,
  };
}

export function DetailCard({
  title,
  titleHint,
  hint,
  icon,
  children,
  className,
  headerActions,
  classNames,
  labels,
}: DetailCardProps) {
  const cardClass = [classNames.card, className].filter(Boolean).join(" ");

  const titleBlock = (
    <>
      <h2 className={classNames.title}>
        {title}
        {titleHint && classNames.titleHelp ? (
          <HelpTooltip
            content={titleHint}
            ariaLabel={labels.titleHelpAriaLabel(title)}
            className={classNames.titleHelp}
          />
        ) : null}
      </h2>
      {hint ? (
        <p className={classNames.hint ?? classNames.description}>{hint}</p>
      ) : null}
    </>
  );

  return (
    <section className={cardClass}>
      <header className={classNames.header}>
        {icon && classNames.icon ? <div className={classNames.icon}>{icon}</div> : null}
        {classNames.heading ? (
          <div className={classNames.heading}>{titleBlock}</div>
        ) : (
          <div>{titleBlock}</div>
        )}
        {headerActions && classNames.actions ? (
          <div className={classNames.actions}>{headerActions}</div>
        ) : null}
      </header>
      {classNames.wrapBody && classNames.body ? (
        <div className={classNames.body}>{children}</div>
      ) : (
        children
      )}
    </section>
  );
}

export type DashboardDetailCardProps = Omit<DetailCardProps, "classNames" | "labels">;

export function createDashboardDetailCard(config: {
  classNames: DetailCardClassNames;
  labels: DetailCardLabels;
}) {
  return function DashboardDetailCard(props: DashboardDetailCardProps) {
    return <DetailCard classNames={config.classNames} labels={config.labels} {...props} />;
  };
}
