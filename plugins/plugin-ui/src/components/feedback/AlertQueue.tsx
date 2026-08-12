import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type AlertQueueTone = "neutral" | "info" | "warning" | "danger";

export type AlertQueueItem = {
  id: string;
  title: ReactNode;
  description?: ReactNode;
  tone?: AlertQueueTone;
  leadingIcon?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
};

export type AlertQueueClassNames = {
  root: string;
  list: string;
  item: string;
  icon: string;
  body: string;
  title: string;
  description: string;
  action: string;
  empty: string;
};

export type AlertQueueProps = {
  items: AlertQueueItem[];
  emptyMessage?: string;
  classNames: AlertQueueClassNames;
  className?: string;
  "aria-label"?: string;
};

export function alertQueueBemClasses(prefix: string): AlertQueueClassNames {
  return {
    root: delpiUiClass(`${prefix}-alert-queue`, "delpi-ui-alert-queue"),
    list: delpiUiClass(`${prefix}-alert-queue__list`, "delpi-ui-alert-queue__list"),
    item: delpiUiClass(`${prefix}-alert-queue__item`, "delpi-ui-alert-queue__item"),
    icon: delpiUiClass(`${prefix}-alert-queue__icon`, "delpi-ui-alert-queue__icon"),
    body: delpiUiClass(`${prefix}-alert-queue__body`, "delpi-ui-alert-queue__body"),
    title: delpiUiClass(`${prefix}-alert-queue__title`, "delpi-ui-alert-queue__title"),
    description: delpiUiClass(
      `${prefix}-alert-queue__description`,
      "delpi-ui-alert-queue__description",
    ),
    action: delpiUiClass(`${prefix}-alert-queue__action`, "delpi-ui-alert-queue__action"),
    empty: delpiUiClass(`${prefix}-alert-queue__empty`, "delpi-ui-alert-queue__empty"),
  };
}

export function AlertQueue({
  items,
  emptyMessage = "Nada precisa de atenção agora.",
  classNames,
  className,
  "aria-label": ariaLabel = "Itens que precisam de atenção",
}: AlertQueueProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  if (!items.length) {
    return (
      <div className={rootClass} role="status" aria-label={ariaLabel}>
        <p className={classNames.empty}>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={rootClass} aria-label={ariaLabel}>
      <ul className={classNames.list}>
        {items.map((item) => {
          const tone = item.tone ?? "neutral";
          const itemClass = withBemModifier(classNames.item, tone);
          return (
            <li key={item.id} className={itemClass}>
              {item.leadingIcon ? (
                <span className={classNames.icon} aria-hidden="true">
                  {item.leadingIcon}
                </span>
              ) : null}
              <div className={classNames.body}>
                <div className={classNames.title}>{item.title}</div>
                {item.description ? (
                  <div className={classNames.description}>{item.description}</div>
                ) : null}
              </div>
              {item.onAction && item.actionLabel ? (
                <button
                  type="button"
                  className={classNames.action}
                  onClick={item.onAction}
                >
                  {item.actionLabel}
                </button>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export type DashboardAlertQueueProps = Omit<AlertQueueProps, "classNames">;

export function createDashboardAlertQueue(config: { prefix: string }) {
  const classNames = alertQueueBemClasses(config.prefix);
  return function DashboardAlertQueue(props: DashboardAlertQueueProps) {
    return <AlertQueue classNames={classNames} {...props} />;
  };
}
