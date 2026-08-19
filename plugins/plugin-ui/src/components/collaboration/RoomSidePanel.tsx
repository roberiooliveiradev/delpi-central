import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type RoomSidePanelClassNames = {
  root: string;
  title: string;
  body: string;
};

export type RoomSidePanelProps = {
  classNames: RoomSidePanelClassNames;
  title: string;
  children: ReactNode;
  /** Quando false, o painel não monta (toggle só no header da thread). */
  open?: boolean;
  className?: string;
};

export function roomSidePanelBemClasses(prefix: string): RoomSidePanelClassNames {
  const base = `${prefix}-room-side-panel`;
  const ui = "delpi-ui-room-side-panel";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    title: pair(`${base}__title`, `${ui}__title`),
    body: pair(`${base}__body`, `${ui}__body`),
  };
}

/**
 * Coluna direita da thread (Teams «Neste chat»): encolhe o chat, sem overlay nem X.
 */
export function RoomSidePanel({
  classNames,
  title,
  children,
  open = true,
  className,
}: RoomSidePanelProps) {
  if (!open) return null;

  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <aside className={rootClass} aria-label={title}>
      <h2 className={classNames.title}>{title}</h2>
      <div className={classNames.body}>{children}</div>
    </aside>
  );
}

export type DashboardRoomSidePanelProps = Omit<RoomSidePanelProps, "classNames">;

export function createDashboardRoomSidePanel(prefix: string) {
  const classNames = roomSidePanelBemClasses(prefix);
  return function DashboardRoomSidePanel(props: DashboardRoomSidePanelProps) {
    return <RoomSidePanel classNames={classNames} {...props} />;
  };
}
