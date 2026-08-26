import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type EmptyGuidanceVariant = "panel" | "canvas";

export type EmptyGuidanceClassNames = {
  rootPanel: string;
  rootCanvas: string;
  icon: string;
  title: string;
  message: string;
  actions: string;
};

export type EmptyGuidanceProps = {
  variant: EmptyGuidanceVariant;
  title: string;
  message?: string;
  icon?: ReactNode;
  children?: ReactNode;
  classNames: EmptyGuidanceClassNames;
  role?: "status" | "alert";
};

export function emptyGuidanceBemClasses(prefix: string): EmptyGuidanceClassNames {
  const base = `${prefix}-empty-guidance`;
  const ui = "delpi-ui-empty-guidance";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    rootPanel: pair(
      `${base} ${base}--panel`,
      `${ui} ${ui}--panel`,
    ),
    rootCanvas: pair(
      `${base} ${base}--canvas`,
      `${ui} ${ui}--canvas`,
    ),
    icon: pair(`${base}__icon`, `${ui}__icon`),
    title: pair(`${base}__title`, `${ui}__title`),
    message: pair(`${base}__message`, `${ui}__message`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
  };
}

/**
 * Unified empty guidance for sidebar panels (inbox) and conversation canvas.
 * Copy and actions are host-provided; kit only supplies layout and tone.
 */
export function EmptyGuidance({
  variant,
  title,
  message,
  icon,
  children,
  classNames,
  role = "status",
}: EmptyGuidanceProps) {
  const rootClass =
    variant === "panel" ? classNames.rootPanel : classNames.rootCanvas;
  const TitleTag = variant === "panel" ? "h3" : "p";

  return (
    <div className={rootClass} role={role}>
      {icon ? (
        <div className={classNames.icon} aria-hidden="true">
          {icon}
        </div>
      ) : null}
      <TitleTag className={classNames.title}>{title}</TitleTag>
      {message ? <p className={classNames.message}>{message}</p> : null}
      {children ? <div className={classNames.actions}>{children}</div> : null}
    </div>
  );
}

export type DashboardEmptyGuidanceProps = Omit<EmptyGuidanceProps, "classNames">;

export function createDashboardEmptyGuidance(prefix: string) {
  const classNames = emptyGuidanceBemClasses(prefix);
  return function DashboardEmptyGuidance(props: DashboardEmptyGuidanceProps) {
    return <EmptyGuidance classNames={classNames} {...props} />;
  };
}
