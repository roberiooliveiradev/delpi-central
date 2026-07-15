import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { delpiUiClass, ensureDelpiUiClass } from "../../utils/delpiUiClass";

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
    card: delpiUiClass(
      `${prefix}-card ${prefix}-detail-card`,
      "delpi-ui-card delpi-ui-detail-card",
    ),
    header: delpiUiClass(`${prefix}-detail-card__header`, "delpi-ui-detail-card__header"),
    icon: `${prefix}-summary-card__icon`,
    title: `${prefix}-summary-card__title`,
    description: `${prefix}-summary-card__description`,
    wrapBody: false,
  };
}

export function detailCardRichBemClasses(prefix: string): DetailCardClassNames {
  const card = `${prefix}-detail-card`;
  const ui = "delpi-ui-detail-card";
  return {
    card: delpiUiClass(`${prefix}-card ${card}`, `delpi-ui-card ${ui}`),
    header: delpiUiClass(`${card}__header`, `${ui}__header`),
    icon: delpiUiClass(`${card}__icon`, `${ui}__icon`),
    heading: delpiUiClass(`${card}__heading`, `${ui}__heading`),
    title: delpiUiClass(`${card}__title`, `${ui}__title`),
    titleHelp: delpiUiClass(`${card}__title-help`, `${ui}__title-help`),
    hint: delpiUiClass(`${card}__hint`, `${ui}__hint`),
    actions: delpiUiClass(
      `${card}__actions ${prefix}-no-print`,
      `${ui}__actions delpi-ui-no-print`,
    ),
    body: delpiUiClass(`${card}__body`, `${ui}__body`),
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
  const withFull =
    className != null && /\b[\w-]*detail-card--full\b/.test(className)
      ? ensureDelpiUiClass(className, "delpi-ui-detail-card--full")
      : className;
  const cardClass = [classNames.card, withFull].filter(Boolean).join(" ");

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
