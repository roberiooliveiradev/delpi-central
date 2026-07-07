import { useId, type ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

export type ChartCardClassNames = {
  section: string;
  header: string;
  /** Envolve título + hint quando o layout tem ações à direita no header. */
  heading?: string;
  title: string;
  titleHelp?: string;
  hint?: string;
  actions?: string;
  body: string;
};

export type ChartCardProps = {
  title: string;
  titleHint?: string;
  hint?: string;
  children: ReactNode;
  headerActions?: ReactNode;
  classNames: ChartCardClassNames;
  className?: string;
  titleLevel?: 2 | 3;
};

/** Monta classNames BEM `{prefix}-chart-card__*` usados pelos dashboards departamentais. */
export function chartCardBemClasses(
  prefix: string,
  options?: {
    withHeading?: boolean;
    withActions?: boolean;
    cardModifier?: string;
  },
): ChartCardClassNames {
  const cardModifier = options?.cardModifier ?? "card";
  const card = `${prefix}-${cardModifier}`;
  const withHeading = options?.withHeading ?? true;
  const withActions = options?.withActions ?? true;

  return {
    section: `${card} ${prefix}-chart-card`,
    header: `${prefix}-chart-card__header`,
    heading: withHeading ? `${prefix}-chart-card__heading` : undefined,
    title: `${prefix}-chart-card__title`,
    titleHelp: `${prefix}-chart-card__title-help`,
    hint: `${prefix}-chart-card__hint`,
    actions: withActions ? `${prefix}-chart-card__actions ${prefix}-no-print` : undefined,
    body: `${prefix}-chart-card__body`,
  };
}

export function ChartCard({
  title,
  titleHint,
  hint,
  children,
  headerActions,
  classNames,
  className,
  titleLevel = 2,
}: ChartCardProps) {
  const titleId = useId();
  const TitleTag = titleLevel === 3 ? "h3" : "h2";
  const sectionClass = [classNames.section, className].filter(Boolean).join(" ");

  const titleNode = (
    <TitleTag id={titleId} className={classNames.title}>
      {title}
      {titleHint ? (
        <HelpTooltip
          content={titleHint}
          ariaLabel={`Ajuda: ${title}`}
          className={classNames.titleHelp}
        />
      ) : null}
    </TitleTag>
  );

  const hintNode =
    hint != null && hint !== "" ? (
      <p className={classNames.hint} id={`${titleId}-hint`}>
        {hint}
      </p>
    ) : null;

  const headingContent = (
    <>
      {titleNode}
      {hintNode}
    </>
  );

  return (
    <section className={sectionClass} aria-labelledby={titleId} role="region">
      <div className={classNames.header}>
        {classNames.heading ? (
          <div className={classNames.heading}>{headingContent}</div>
        ) : (
          headingContent
        )}
        {headerActions && classNames.actions ? (
          <div className={classNames.actions}>{headerActions}</div>
        ) : null}
      </div>
      <div
        className={classNames.body}
        aria-describedby={hint ? `${titleId}-hint` : undefined}
      >
        {children}
      </div>
    </section>
  );
}
