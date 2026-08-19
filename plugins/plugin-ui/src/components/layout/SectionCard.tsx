import { ChevronDown, ChevronUp } from "lucide-react";
import { useId, useState, type ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type SectionCardClassNames = {
  section: string;
  header: string;
  title: string;
  titleWithHelp: string;
  subtitle: string;
  actions: string;
  body?: string;
  collapseToggle?: string;
};

export type SectionCardLabels = {
  titleHelpAriaLabel: (title: string) => string;
  expandAriaLabel?: (title: string) => string;
  collapseAriaLabel?: (title: string) => string;
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
  /** Quando true, o corpo pode ser ocultado pelo toggle no header. */
  collapsible?: boolean;
  /** Estado inicial (não controlado). Default: true (aberto). */
  defaultOpen?: boolean;
  /** Controle externo do aberto/fechado. */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
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
    body: pair(`${section}__body`, `${ui}__body`),
    collapseToggle: pair(`${section}__collapse-toggle`, `${ui}__collapse-toggle`),
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
    body: pair(`${section}__body`, `${ui}__body`),
    collapseToggle: pair(`${section}__collapse-toggle`, `${ui}__collapse-toggle`),
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
  collapsible = false,
  defaultOpen = true,
  open: openProp,
  onOpenChange,
}: SectionCardProps) {
  const bodyId = useId();
  const [uncontrolledOpen, setUncontrolledOpen] = useState(defaultOpen);
  const isControlled = openProp !== undefined;
  const isOpen = isControlled ? Boolean(openProp) : uncontrolledOpen;

  const setOpen = (next: boolean) => {
    if (!isControlled) setUncontrolledOpen(next);
    onOpenChange?.(next);
  };

  const sectionClass = [
    classNames.section,
    collapsible && !isOpen ? "delpi-ui-section-card--collapsed" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const expandLabel =
    labels.expandAriaLabel?.(title) ?? `Expandir seção ${title}`;
  const collapseLabel =
    labels.collapseAriaLabel?.(title) ?? `Recolher seção ${title}`;

  return (
    <section className={sectionClass}>
      <div className={classNames.header}>
        <div>
          <h2 className={classNames.title}>
            <span className={classNames.titleWithHelp}>
              {hint ? (
                <HelpTooltip
                  content={hint}
                  ariaLabel={labels.titleHelpAriaLabel(title)}
                  wrap
                  placement="bottom"
                >
                  <span className="delpi-ui-section-hint-label">{title}</span>
                </HelpTooltip>
              ) : (
                <span>{title}</span>
              )}
              {collapsible ? (
                <button
                  type="button"
                  className={classNames.collapseToggle}
                  aria-expanded={isOpen}
                  aria-controls={bodyId}
                  aria-label={isOpen ? collapseLabel : expandLabel}
                  onClick={() => setOpen(!isOpen)}
                >
                  {isOpen ? (
                    <ChevronUp size={18} strokeWidth={2} aria-hidden />
                  ) : (
                    <ChevronDown size={18} strokeWidth={2} aria-hidden />
                  )}
                </button>
              ) : null}
            </span>
          </h2>
          {subtitle ? <p className={classNames.subtitle}>{subtitle}</p> : null}
        </div>
        {actions ? <div className={classNames.actions}>{actions}</div> : null}
      </div>
      {collapsible ? (
        isOpen ? (
          <div id={bodyId} className={classNames.body}>
            {children}
          </div>
        ) : (
          <div id={bodyId} className={classNames.body} hidden />
        )
      ) : (
        children
      )}
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
