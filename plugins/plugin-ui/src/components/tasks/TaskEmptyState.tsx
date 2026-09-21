import type { ReactNode } from "react";

import { EmptyState, emptyStatePanelBemClasses } from "../feedback/EmptyState";

export type TaskEmptyStateProps = {
  title?: string;
  message: string;
  children?: ReactNode;
  role?: "status" | "alert";
};

const EMPTY = emptyStatePanelBemClasses("delpi-ui");

/** Empty da fila. O texto e o CTA vêm do portal. */
export function TaskEmptyState({ title, message, children, role = "status" }: TaskEmptyStateProps) {
  return (
    <EmptyState classNames={EMPTY} title={title} defaultMessage={message} role={role}>
      {children ? <div className="delpi-ui-task-empty__action">{children}</div> : null}
    </EmptyState>
  );
}
