import type { ReactNode } from "react";

export type TaskCardListProps = {
  children: ReactNode;
  ariaLabel?: string;
  ariaBusy?: boolean;
};

/** Vertical semantic list of task cards — spacing + list semantics only. */
export function TaskCardList({ children, ariaLabel, ariaBusy }: TaskCardListProps) {
  return (
    <div
      className="delpi-ui-task-card-list"
      role="list"
      aria-label={ariaLabel ?? "Tarefas"}
      aria-busy={ariaBusy || undefined}
    >
      {children}
    </div>
  );
}
