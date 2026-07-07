import type { ReactNode } from "react";

export type InfoStateClassNames = {
  root: string;
  icon: string;
  content: string;
  title: string;
  description: string;
  action: string;
};

export type InfoStatePanelProps = {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon: ReactNode;
  classNames: InfoStateClassNames;
};

export function infoStateBemClasses(prefix: string): InfoStateClassNames {
  const base = `${prefix}-info-state`;

  return {
    root: base,
    icon: `${base}__icon`,
    content: `${base}__content`,
    title: `${base}__title`,
    description: `${base}__description`,
    action: `${base}__action`,
  };
}

export function InfoStatePanel({
  title,
  description,
  actionLabel,
  onAction,
  icon,
  classNames,
}: InfoStatePanelProps) {
  const shouldRenderAction = Boolean(actionLabel && onAction);

  return (
    <div className={classNames.root}>
      <div className={classNames.icon}>{icon}</div>
      <div className={classNames.content}>
        <h3 className={classNames.title}>{title}</h3>
        <p className={classNames.description}>{description}</p>
        {shouldRenderAction ? (
          <button type="button" className={classNames.action} onClick={onAction}>
            {actionLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}

export type DashboardInfoStatePanelProps = Omit<InfoStatePanelProps, "classNames" | "icon">;

export function createInfoStatePanel(config: { prefix: string; renderIcon: () => ReactNode }) {
  const classNames = infoStateBemClasses(config.prefix);

  return function DashboardInfoStatePanel(props: DashboardInfoStatePanelProps) {
    return (
      <InfoStatePanel icon={config.renderIcon()} classNames={classNames} {...props} />
    );
  };
}
