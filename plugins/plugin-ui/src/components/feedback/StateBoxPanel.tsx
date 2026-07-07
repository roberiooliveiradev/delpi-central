import type { ReactNode } from "react";

export type StateBoxVariant = "loading" | "error" | "empty";

export type StateBoxClassNames = {
  root: string;
  rootLoading: string;
  rootError: string;
  rootEmpty: string;
  icon: string;
};

export type StateBoxPanelProps = {
  variant: StateBoxVariant;
  title: string;
  message?: string;
  action?: ReactNode;
  icon: ReactNode;
  iconClassName?: string;
  classNames: StateBoxClassNames;
};

export function stateBoxBemClasses(prefix: string): StateBoxClassNames {
  const base = `${prefix}-state-box`;

  return {
    root: base,
    rootLoading: `${base} ${base}--loading`,
    rootError: `${base} ${base}--error`,
    rootEmpty: `${base} ${base}--empty`,
    icon: `${base}__icon`,
  };
}

function resolveRootClass(variant: StateBoxVariant, classNames: StateBoxClassNames): string {
  if (variant === "error") return classNames.rootError;
  if (variant === "empty") return classNames.rootEmpty;
  return classNames.rootLoading;
}

export function StateBoxPanel({
  variant,
  title,
  message,
  action,
  icon,
  iconClassName,
  classNames,
}: StateBoxPanelProps) {
  const iconClass = [classNames.icon, iconClassName].filter(Boolean).join(" ");

  return (
    <div className={resolveRootClass(variant, classNames)} role="status">
      <span className={iconClass} aria-hidden="true">
        {icon}
      </span>
      <div>
        <h2>{title}</h2>
        {message ? <p>{message}</p> : null}
      </div>
      {action}
    </div>
  );
}

export type DashboardStateBoxPanelProps = Omit<StateBoxPanelProps, "classNames" | "icon">;

export function createStateBoxPanel(config: {
  prefix: string;
  renderIcon: (variant: StateBoxVariant) => ReactNode;
  iconClassName?: (variant: StateBoxVariant) => string | undefined;
}) {
  const classNames = stateBoxBemClasses(config.prefix);

  return function DashboardStateBoxPanel(props: DashboardStateBoxPanelProps) {
    return (
      <StateBoxPanel
        icon={config.renderIcon(props.variant)}
        iconClassName={config.iconClassName?.(props.variant)}
        classNames={classNames}
        {...props}
      />
    );
  };
}
