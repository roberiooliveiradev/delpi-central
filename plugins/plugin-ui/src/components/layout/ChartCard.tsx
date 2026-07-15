import { useId, type ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type ChartCardClassNames = {
  section: string;
  header: string;
  /** Envolve título + hint quando o layout tem ações à direita no header. */
  heading?: string;
  /** Linha título + ações; hint fica abaixo (ex.: controle-retrabalhos). */
  headerRow?: string;
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

/** Monta classNames BEM `{prefix}-chart-card__*` + `.delpi-ui-chart-card*`. */
export function chartCardBemClasses(
  prefix: string,
  options?: {
    withHeading?: boolean;
    withActions?: boolean;
    cardModifier?: string;
    /** `titleRow`: título e ações na mesma linha; hint abaixo. */
    headerLayout?: "default" | "titleRow";
  },
): ChartCardClassNames {
  const cardModifier = options?.cardModifier ?? "card";
  const card = `${prefix}-${cardModifier}`;
  const ui = "delpi-ui-chart-card";
  const headerLayout = options?.headerLayout ?? "default";
  const withHeading = options?.withHeading ?? headerLayout === "default";
  const withActions = options?.withActions ?? true;
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    section: pair(`${card} ${prefix}-chart-card`, `delpi-ui-card ${ui}`),
    header: pair(`${prefix}-chart-card__header`, `${ui}__header`),
    heading:
      headerLayout === "default" && withHeading
        ? pair(`${prefix}-chart-card__heading`, `${ui}__heading`)
        : undefined,
    headerRow:
      headerLayout === "titleRow"
        ? pair(`${prefix}-chart-card__header-row`, `${ui}__header-row`)
        : undefined,
    title: pair(`${prefix}-chart-card__title`, `${ui}__title`),
    titleHelp: pair(`${prefix}-chart-card__title-help`, `${ui}__title-help`),
    hint: pair(`${prefix}-chart-card__hint`, `${ui}__hint`),
    actions: withActions
      ? pair(
          `${prefix}-chart-card__actions ${prefix}-no-print`,
          `${ui}__actions delpi-ui-no-print`,
        )
      : undefined,
    body: pair(`${prefix}-chart-card__body`, `${ui}__body`),
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
      {!classNames.headerRow ? hintNode : null}
    </>
  );

  const headerContent = classNames.headerRow ? (
    <>
      <div className={classNames.headerRow}>
        {titleNode}
        {headerActions && classNames.actions ? (
          <div className={classNames.actions}>{headerActions}</div>
        ) : null}
      </div>
      {hintNode}
    </>
  ) : (
    <>
      {classNames.heading ? (
        <div className={classNames.heading}>{headingContent}</div>
      ) : (
        headingContent
      )}
      {headerActions && classNames.actions ? (
        <div className={classNames.actions}>{headerActions}</div>
      ) : null}
    </>
  );

  return (
    <section className={sectionClass} aria-labelledby={titleId} role="region">
      <div className={classNames.header}>{headerContent}</div>
      <div
        className={classNames.body}
        aria-describedby={hint ? `${titleId}-hint` : undefined}
      >
        {children}
      </div>
    </section>
  );
}
