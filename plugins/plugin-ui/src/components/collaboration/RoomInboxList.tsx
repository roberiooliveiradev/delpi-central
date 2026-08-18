import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type RoomInboxListItem = {
  id: string;
  title: string;
  preview?: string | null;
  metaLabel?: string | null;
  kindLabel?: string | null;
  unreadCount?: number;
  mentioned?: boolean;
  selected?: boolean;
};

export type RoomInboxListClassNames = {
  root: string;
  list: string;
  item: string;
  itemSelected: string;
  itemUnread: string;
  title: string;
  preview: string;
  meta: string;
  badge: string;
  empty: string;
};

export type RoomInboxListProps = {
  items: readonly RoomInboxListItem[];
  classNames: RoomInboxListClassNames;
  listAriaLabel: string;
  emptyLabel: string;
  unreadBadgeLabel?: (count: number) => string;
  onSelect?: (id: string) => void;
  trailing?: (item: RoomInboxListItem) => ReactNode;
  className?: string;
};

export function roomInboxListBemClasses(prefix: string): RoomInboxListClassNames {
  const base = `${prefix}-room-inbox`;
  const ui = "delpi-ui-room-inbox";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    list: pair(`${base}__list`, `${ui}__list`),
    item: pair(`${base}__item`, `${ui}__item`),
    itemSelected: pair(
      `${base}__item ${base}__item--selected`,
      `${ui}__item ${ui}__item--selected`,
    ),
    itemUnread: pair(
      `${base}__item ${base}__item--unread`,
      `${ui}__item ${ui}__item--unread`,
    ),
    title: pair(`${base}__title`, `${ui}__title`),
    preview: pair(`${base}__preview`, `${ui}__preview`),
    meta: pair(`${base}__meta`, `${ui}__meta`),
    badge: pair(`${base}__badge`, `${ui}__badge`),
    empty: pair(`${base}__empty`, `${ui}__empty`),
  };
}

function itemClassName(
  classNames: RoomInboxListClassNames,
  item: RoomInboxListItem,
): string {
  if (item.selected) return classNames.itemSelected;
  if ((item.unreadCount ?? 0) > 0 || item.mentioned) return classNames.itemUnread;
  return classNames.item;
}

/**
 * Inbox list for interaction rooms — not WorklistItem (day queue).
 */
export function RoomInboxList({
  items,
  classNames,
  listAriaLabel,
  emptyLabel,
  unreadBadgeLabel,
  onSelect,
  trailing,
  className,
}: RoomInboxListProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  if (items.length === 0) {
    return (
      <div className={rootClass}>
        <div className={classNames.empty} role="status">
          {emptyLabel}
        </div>
      </div>
    );
  }

  return (
    <div className={rootClass}>
      <ul className={classNames.list} aria-label={listAriaLabel}>
        {items.map((item) => {
          const unread = item.unreadCount ?? 0;
          return (
            <li key={item.id}>
              <button
                type="button"
                className={itemClassName(classNames, item)}
                aria-current={item.selected ? "true" : undefined}
                onClick={() => onSelect?.(item.id)}
              >
                <div className={classNames.title}>{item.title}</div>
                {item.preview ? (
                  <div className={classNames.preview}>{item.preview}</div>
                ) : null}
                <div className={classNames.meta}>
                  {item.kindLabel ? <span>{item.kindLabel}</span> : null}
                  {item.metaLabel ? <span>{item.metaLabel}</span> : null}
                  {unread > 0 ? (
                    <span className={classNames.badge}>
                      {unreadBadgeLabel ? unreadBadgeLabel(unread) : unread}
                    </span>
                  ) : null}
                  {trailing?.(item)}
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export type DashboardRoomInboxListProps = Omit<RoomInboxListProps, "classNames">;

export function createDashboardRoomInboxList(prefix: string) {
  const classNames = roomInboxListBemClasses(prefix);
  return function DashboardRoomInboxList(props: DashboardRoomInboxListProps) {
    return <RoomInboxList classNames={classNames} {...props} />;
  };
}
