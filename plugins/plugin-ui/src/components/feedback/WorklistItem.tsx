import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type WorklistItemTone = "neutral" | "info" | "warning" | "danger" | "success";

export type WorklistItemClassNames = {
  root: string;
  icon: string;
  body: string;
  title: string;
  meta: string;
  detail: string;
  actions: string;
  action: string;
};

export type WorklistItemProps = {
  title: ReactNode;
  meta?: ReactNode;
  /** Nota / observação (padrão CRM: notes visíveis na fila). */
  detail?: ReactNode;
  tone?: WorklistItemTone;
  leadingIcon?: ReactNode;
  primaryActionLabel?: string;
  onPrimaryAction?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
  tertiaryActionLabel?: string;
  onTertiaryAction?: () => void;
  quaternaryActionLabel?: string;
  onQuaternaryAction?: () => void;
  /** Ações extras (ex.: Editar) antes dos botões nomeados. */
  extraActions?: ReactNode;
  classNames: WorklistItemClassNames;
  className?: string;
};

export function worklistItemBemClasses(prefix: string): WorklistItemClassNames {
  return {
    root: delpiUiClass(`${prefix}-worklist-item`, "delpi-ui-worklist-item"),
    icon: delpiUiClass(`${prefix}-worklist-item__icon`, "delpi-ui-worklist-item__icon"),
    body: delpiUiClass(`${prefix}-worklist-item__body`, "delpi-ui-worklist-item__body"),
    title: delpiUiClass(`${prefix}-worklist-item__title`, "delpi-ui-worklist-item__title"),
    meta: delpiUiClass(`${prefix}-worklist-item__meta`, "delpi-ui-worklist-item__meta"),
    detail: delpiUiClass(`${prefix}-worklist-item__detail`, "delpi-ui-worklist-item__detail"),
    actions: delpiUiClass(`${prefix}-worklist-item__actions`, "delpi-ui-worklist-item__actions"),
    action: delpiUiClass(`${prefix}-worklist-item__action`, "delpi-ui-worklist-item__action"),
  };
}

export function WorklistItem({
  title,
  meta,
  detail,
  tone = "neutral",
  leadingIcon,
  primaryActionLabel,
  onPrimaryAction,
  secondaryActionLabel,
  onSecondaryAction,
  tertiaryActionLabel,
  onTertiaryAction,
  quaternaryActionLabel,
  onQuaternaryAction,
  extraActions,
  classNames,
  className,
}: WorklistItemProps) {
  const rootClass = [withBemModifier(classNames.root, tone), className]
    .filter(Boolean)
    .join(" ");

  const hasActions =
    Boolean(extraActions) ||
    Boolean(primaryActionLabel) ||
    Boolean(secondaryActionLabel) ||
    Boolean(tertiaryActionLabel) ||
    Boolean(quaternaryActionLabel);

  return (
    <div className={rootClass}>
      {leadingIcon ? (
        <span className={classNames.icon} aria-hidden="true">
          {leadingIcon}
        </span>
      ) : null}
      <div className={classNames.body}>
        <div className={classNames.title}>{title}</div>
        {meta ? <div className={classNames.meta}>{meta}</div> : null}
        {detail ? <div className={classNames.detail}>{detail}</div> : null}
      </div>
      {hasActions ? (
        <div className={classNames.actions}>
          {extraActions}
          {quaternaryActionLabel && onQuaternaryAction ? (
            <button
              type="button"
              className={withBemModifier(classNames.action, "ghost")}
              onClick={onQuaternaryAction}
            >
              {quaternaryActionLabel}
            </button>
          ) : null}
          {tertiaryActionLabel && onTertiaryAction ? (
            <button
              type="button"
              className={withBemModifier(classNames.action, "ghost")}
              onClick={onTertiaryAction}
            >
              {tertiaryActionLabel}
            </button>
          ) : null}
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
