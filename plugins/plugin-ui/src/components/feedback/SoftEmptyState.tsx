import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type SoftEmptyStateClassNames = {
  root: string;
  icon: string;
  title: string;
  message: string;
};

export type SoftEmptyStateProps = {
  classNames: SoftEmptyStateClassNames;
  title: string;
  message?: string;
  icon?: ReactNode;
  role?: "status" | "alert";
};

export function softEmptyStateBemClasses(prefix: string): SoftEmptyStateClassNames {
  const base = `${prefix}-soft-empty`;
  const ui = "delpi-ui-soft-empty";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    icon: pair(`${base}__icon`, `${ui}__icon`),
    title: pair(`${base}__title`, `${ui}__title`),
    message: pair(`${base}__message`, `${ui}__message`),
  };
}

/**
 * Centered soft empty hint (icon + muted copy) — conversation / canvas style.
 * No card border; fills parent when parent is a flex column.
 */
export function SoftEmptyState({
  classNames,
  title,
  message,
  icon,
  role = "status",
}: SoftEmptyStateProps) {
  return (
    <div className={classNames.root} role={role}>
      {icon ? (
        <div className={classNames.icon} aria-hidden="true">
          {icon}
        </div>
      ) : null}
      <p className={classNames.title}>{title}</p>
      {message ? <p className={classNames.message}>{message}</p> : null}
    </div>
  );
}

export type DashboardSoftEmptyStateProps = Omit<SoftEmptyStateProps, "classNames">;

export function createDashboardSoftEmptyState(prefix: string) {
  const classNames = softEmptyStateBemClasses(prefix);
  return function DashboardSoftEmptyState(props: DashboardSoftEmptyStateProps) {
    return <SoftEmptyState classNames={classNames} {...props} />;
  };
}
