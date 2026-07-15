import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type SectionCardClassNames = {
  section: string;
  header: string;
  title: string;
  titleWithHelp: string;
  subtitle: string;
  actions: string;
};

export type SectionCardLabels = {
  titleHelpAriaLabel: (title: string) => string;
};

export type SectionCardProps = {
  title: string;
  subtitle?: string;
  hint?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
  classNames: SectionCardClassNames;
  labels: SectionCardLabels;
};

export function sectionCardPacBemClasses(prefix: string): SectionCardClassNames {
  const section = `${prefix}-section-card`;
  const ui = "delpi-ui-section-card";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    section: pair(`${prefix}-card ${section}`, `delpi-ui-card ${ui}`),
    header: pair(`${section}__header`, `${ui}__header`),
    title: pair(`${prefix}-section-title`, "delpi-ui-section-title"),
    titleWithHelp: pair(`${prefix}-title-with-help`, `${ui}__title-with-help`),
    subtitle: pair(`${prefix}-muted ${prefix}-section-subtitle`, `${ui}__subtitle`),
    actions: pair(`${section}__actions`, `${ui}__actions`),
  };
}

export function sectionCardKaizenBemClasses(prefix: string): SectionCardClassNames {
  const section = `${prefix}-section-card`;
  const ui = "delpi-ui-section-card";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    section: pair(`${prefix}-card ${section}`, `delpi-ui-card ${ui}`),
    header: pair(`${section}__header`, `${ui}__header`),
    title: pair(`${section}__title`, `${ui}__title`),
    titleWithHelp: pair(`${prefix}-title-with-help`, `${ui}__title-with-help`),
    subtitle: pair(`${section}__desc`, `${ui}__subtitle`),
    actions: pair(`${section}__actions`, `${ui}__actions`),
  };
}

export function SectionCard({
  title,
  subtitle,
  hint,
  children,
  actions,
  className,
  classNames,
  labels,
}: SectionCardProps) {
  const sectionClass = [classNames.section, className].filter(Boolean).join(" ");

  return (
    <section className={sectionClass}>
      <div className={classNames.header}>
        <div>
          <h2 className={classNames.title}>
            <span className={classNames.titleWithHelp}>
              <span>{title}</span>
              {hint ? (
                <HelpTooltip
                  content={hint}
                  ariaLabel={labels.titleHelpAriaLabel(title)}
                />
              ) : null}
            </span>
          </h2>
          {subtitle ? <p className={classNames.subtitle}>{subtitle}</p> : null}
        </div>
        {actions ? <div className={classNames.actions}>{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}

export type DashboardSectionCardProps = Omit<SectionCardProps, "classNames" | "labels">;

export function createDashboardSectionCard(config: {
  classNames: SectionCardClassNames;
  labels: SectionCardLabels;
}) {
  return function DashboardSectionCard(props: DashboardSectionCardProps) {
    return <SectionCard classNames={config.classNames} labels={config.labels} {...props} />;
  };
}
