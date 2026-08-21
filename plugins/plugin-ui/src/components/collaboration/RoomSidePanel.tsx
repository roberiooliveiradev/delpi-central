import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type RoomSidePanelClassNames = {
  root: string;
  collapsed: string;
  title: string;
  body: string;
};

export type RoomSidePanelProps = {
  classNames: RoomSidePanelClassNames;
  title: string;
  children: ReactNode;
  /** When false, panel stays mounted but collapsed (soft width/opacity transition). */
  open?: boolean;
  className?: string;
};

export function roomSidePanelBemClasses(prefix: string): RoomSidePanelClassNames {
  const base = `${prefix}-room-side-panel`;
  const ui = "delpi-ui-room-side-panel";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    collapsed: pair(`${base}--collapsed`, `${ui}--collapsed`),
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
  const rootClass = [
    classNames.root,
    open ? null : classNames.collapsed,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <aside className={rootClass} aria-label={title} aria-hidden={!open}>
      {open ? (
        <>
          <h2 className={classNames.title}>{title}</h2>
          <div className={classNames.body}>{children}</div>
        </>
      ) : null}
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
