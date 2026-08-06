import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type WorklistItemTone = "neutral" | "info" | "warning" | "danger" | "success";

export type WorklistItemClassNames = {
  root: string;
  body: string;
  title: string;
  meta: string;
  actions: string;
  action: string;
};

export type WorklistItemProps = {
  title: ReactNode;
  meta?: ReactNode;
  tone?: WorklistItemTone;
  primaryActionLabel?: string;
  onPrimaryAction?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
  classNames: WorklistItemClassNames;
  className?: string;
};

export function worklistItemBemClasses(prefix: string): WorklistItemClassNames {
  return {
    root: delpiUiClass(`${prefix}-worklist-item`, "delpi-ui-worklist-item"),
    body: delpiUiClass(`${prefix}-worklist-item__body`, "delpi-ui-worklist-item__body"),
    title: delpiUiClass(`${prefix}-worklist-item__title`, "delpi-ui-worklist-item__title"),
    meta: delpiUiClass(`${prefix}-worklist-item__meta`, "delpi-ui-worklist-item__meta"),
    actions: delpiUiClass(`${prefix}-worklist-item__actions`, "delpi-ui-worklist-item__actions"),
    action: delpiUiClass(`${prefix}-worklist-item__action`, "delpi-ui-worklist-item__action"),
  };
}

export function WorklistItem({
  title,
  meta,
  tone = "neutral",
  primaryActionLabel,
  onPrimaryAction,
  secondaryActionLabel,
  onSecondaryAction,
  classNames,
  className,
}: WorklistItemProps) {
  const rootClass = [withBemModifier(classNames.root, tone), className]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass}>
      <div className={classNames.body}>
        <div className={classNames.title}>{title}</div>
        {meta ? <div className={classNames.meta}>{meta}</div> : null}
      </div>
      {primaryActionLabel || secondaryActionLabel ? (
        <div className={classNames.actions}>
          {secondaryActionLabel && onSecondaryAction ? (
            <button
              type="button"
              className={withBemModifier(classNames.action, "ghost")}
              onClick={onSecondaryAction}
            >
              {secondaryActionLabel}
            </button>
          ) : null}
          {primaryActionLabel && onPrimaryAction ? (
            <button
              type="button"
              className={withBemModifier(classNames.action, "primary")}
              onClick={onPrimaryAction}
            >
              {primaryActionLabel}
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export type DashboardWorklistItemProps = Omit<WorklistItemProps, "classNames">;

export function createDashboardWorklistItem(config: { prefix: string }) {
  const classNames = worklistItemBemClasses(config.prefix);
  return function DashboardWorklistItem(props: DashboardWorklistItemProps) {
    return <WorklistItem classNames={classNames} {...props} />;
  };
}
