import { HelpTooltip } from "./HelpTooltip";

export type TitleWithHelpClassNames = {
  root: string;
};

export type TitleWithHelpLabels = {
  titleHelpAriaLabel: (title: string) => string;
};

export type TitleWithHelpProps = {
  title: string;
  hint?: string;
  className?: string;
  classNames: TitleWithHelpClassNames;
  labels: TitleWithHelpLabels;
};

export function titleWithHelpBemClasses(prefix: string): TitleWithHelpClassNames {
  return {
    root: `${prefix}-title-with-help`,
  };
}

export const titleWithHelpPacClasses = titleWithHelpBemClasses;

export function TitleWithHelp({
  title,
  hint,
  className,
  classNames,
  labels,
}: TitleWithHelpProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <span className={rootClass}>
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
    </span>
  );
}

export type DashboardTitleWithHelpProps = Omit<TitleWithHelpProps, "classNames" | "labels">;

export function createDashboardTitleWithHelp(config: {
  classNames: TitleWithHelpClassNames;
  labels: TitleWithHelpLabels;
}) {
  return function DashboardTitleWithHelp(props: DashboardTitleWithHelpProps) {
    return (
      <TitleWithHelp classNames={config.classNames} labels={config.labels} {...props} />
    );
  };
}
