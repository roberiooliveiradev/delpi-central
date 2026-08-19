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
  hit: string;
  row: string;
  leading: string;
  body: string;
  titleRow: string;
  title: string;
  subtitle: string;
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
  leading?: (item: RoomInboxListItem) => ReactNode;
  subtitle?: (item: RoomInboxListItem) => ReactNode;
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
    hit: pair(`${base}__hit`, `${ui}__hit`),
    row: pair(`${base}__row`, `${ui}__row`),
    leading: pair(`${base}__leading`, `${ui}__leading`),
    body: pair(`${base}__body`, `${ui}__body`),
    titleRow: pair(`${base}__title-row`, `${ui}__title-row`),
    title: pair(`${base}__title`, `${ui}__title`),
    subtitle: pair(`${base}__subtitle`, `${ui}__subtitle`),
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
  const unread = (item.unreadCount ?? 0) > 0 || item.mentioned;
  if (item.selected && unread) {
    return `${classNames.itemSelected} ${classNames.itemUnread}`;
  }
  if (item.selected) return classNames.itemSelected;
  if (unread) return classNames.itemUnread;
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
  leading,
  subtitle,
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
          const leadingNode = leading?.(item);
          const subtitleNode = subtitle?.(item);
          const trailingNode = trailing?.(item);
          const hasMeta =
            unread > 0 || Boolean(item.metaLabel) || trailingNode != null;
          return (
            <li key={item.id}>
              <div className={itemClassName(classNames, item)}>
                <button
                  type="button"
                  className={classNames.hit}
                  aria-label={item.title}
                  aria-current={item.selected ? "true" : undefined}
                  onClick={() => onSelect?.(item.id)}
                />
                <div className={classNames.row}>
                  {leadingNode ? (
                    <div className={classNames.leading}>{leadingNode}</div>
                  ) : null}
                  <div className={classNames.body}>
                    <div className={classNames.titleRow}>
                      <div className={classNames.title}>{item.title}</div>
                      {hasMeta ? (
                        <div className={classNames.meta}>
                          {unread > 0 ? (
                            <span className={classNames.badge}>
                              {unreadBadgeLabel ? unreadBadgeLabel(unread) : unread}
                            </span>
                          ) : null}
                          {item.metaLabel ? <span>{item.metaLabel}</span> : null}
                          {trailingNode}
                        </div>
                      ) : null}
                    </div>
                    {subtitleNode ? (
                      <div className={classNames.subtitle}>{subtitleNode}</div>
                    ) : item.kindLabel ? (
                      <div className={classNames.subtitle}>{item.kindLabel}</div>
                    ) : null}
                    {item.preview ? (
                      <div className={classNames.preview}>{item.preview}</div>
                    ) : null}
                  </div>
                </div>
              </div>
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
