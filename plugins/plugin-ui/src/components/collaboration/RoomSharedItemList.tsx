import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type RoomSharedItem = {
  id: string;
  title: string;
  subtitle?: string | null;
  whenLabel?: string | null;
  whoLabel?: string | null;
  ariaLabel: string;
};

export type RoomSharedItemListClassNames = {
  root: string;
  toolbar: string;
  toolbarActions: string;
  list: string;
  row: string;
  icon: string;
  meta: string;
  title: string;
  subtitle: string;
  when: string;
  who: string;
  whoName: string;
};

export type RoomSharedItemListProps = {
  items: readonly RoomSharedItem[];
  classNames: RoomSharedItemListClassNames;
  listAriaLabel: string;
  onOpen: (id: string) => void;
  toolbar?: ReactNode;
  toolbarActions?: ReactNode;
  icon?: (item: RoomSharedItem) => ReactNode;
  whoLeading?: (item: RoomSharedItem) => ReactNode;
  children?: ReactNode;
};

export function roomSharedItemListBemClasses(prefix: string): RoomSharedItemListClassNames {
  const base = `${prefix}-room-shared-items`;
  const ui = "delpi-ui-room-shared-items";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    toolbar: pair(`${base}__toolbar`, `${ui}__toolbar`),
    toolbarActions: pair(`${base}__toolbar-actions`, `${ui}__toolbar-actions`),
    list: pair(`${base}__list`, `${ui}__list`),
    row: pair(`${base}__row`, `${ui}__row`),
    icon: pair(`${base}__icon`, `${ui}__icon`),
    meta: pair(`${base}__meta`, `${ui}__meta`),
    title: pair(`${base}__title`, `${ui}__title`),
    subtitle: pair(`${base}__subtitle`, `${ui}__subtitle`),
    when: pair(`${base}__when`, `${ui}__when`),
    who: pair(`${base}__who`, `${ui}__who`),
    whoName: pair(`${base}__who-name`, `${ui}__who-name`),
  };
}

/** Lista de arquivos/links compartilhados. Não busca, não baixa e não autoriza. */
export function RoomSharedItemList({
  items,
  classNames,
  listAriaLabel,
  onOpen,
  toolbar,
  toolbarActions,
  icon,
  whoLeading,
  children,
}: RoomSharedItemListProps) {
  return (
    <div className={classNames.root}>
      {toolbar || toolbarActions ? (
        <div className={classNames.toolbar}>
          {toolbar}
          {toolbarActions ? <div className={classNames.toolbarActions}>{toolbarActions}</div> : null}
        </div>
      ) : null}
      {items.length > 0 ? (
        <ul className={classNames.list} aria-label={listAriaLabel}>
          {items.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className={classNames.row}
                aria-label={item.ariaLabel}
                onClick={() => onOpen(item.id)}
              >
                <span className={classNames.icon} aria-hidden>
                  {icon?.(item)}
                </span>
                <span className={classNames.meta}>
                  <span className={classNames.title}>{item.title}</span>
                  {item.subtitle ? <span className={classNames.subtitle}>{item.subtitle}</span> : null}
                </span>
                {item.whenLabel ? <span className={classNames.when}>{item.whenLabel}</span> : null}
                <span className={classNames.who}>
                  {whoLeading?.(item)}
                  {item.whoLabel ? <span className={classNames.whoName}>{item.whoLabel}</span> : null}
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : (
        children
      )}
    </div>
  );
}

export type DashboardRoomSharedItemListProps = Omit<RoomSharedItemListProps, "classNames">;

export function createDashboardRoomSharedItemList(prefix: string) {
  const classNames = roomSharedItemListBemClasses(prefix);
  return function DashboardRoomSharedItemList(props: DashboardRoomSharedItemListProps) {
    return <RoomSharedItemList classNames={classNames} {...props} />;
  };
}
