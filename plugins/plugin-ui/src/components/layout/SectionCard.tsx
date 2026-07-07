import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

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
  return {
    section: `${prefix}-card ${section}`,
    header: `${section}__header`,
    title: `${prefix}-section-title`,
    titleWithHelp: `${prefix}-title-with-help`,
    subtitle: `${prefix}-muted ${prefix}-section-subtitle`,
    actions: `${section}__actions`,
  };
}

export function sectionCardKaizenBemClasses(prefix: string): SectionCardClassNames {
  const section = `${prefix}-section-card`;
  return {
    section: `${prefix}-card ${section}`,
    header: `${section}__header`,
    title: `${section}__title`,
    titleWithHelp: `${prefix}-title-with-help`,
    subtitle: `${section}__desc`,
    actions: `${section}__actions`,
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
