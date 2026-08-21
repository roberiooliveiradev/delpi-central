import { Search, X } from "lucide-react";
import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  InitialsAvatar,
  initialsAvatarBemClasses,
  type InitialsAvatarClassNames,
} from "../layout/InitialsAvatar";
import {
  buildFindSnippet,
  splitFindHighlightSegments,
} from "./roomMessageFindHighlight";

export type RoomMessageFindAuthorAvatar = {
  name: string;
  imageUrl?: string | null;
};

export type RoomMessageFindResult = {
  id: string;
  messageId: string;
  authorLabel: string;
  dateLabel?: string | null;
  bodyText: string;
  groupLabel?: string | null;
  authorAvatar?: RoomMessageFindAuthorAvatar | null;
};

export type RoomMessageFindPanelLabels = {
  title: string;
  closeAriaLabel: string;
  placeholder: string;
  clear: string;
  empty: string;
  loading: string;
};

export type RoomMessageFindPanelClassNames = {
  root: string;
  header: string;
  title: string;
  close: string;
  searchRow: string;
  input: string;
  clear: string;
  list: string;
  group: string;
  item: string;
  itemMeta: string;
  itemAuthorRow: string;
  itemAuthor: string;
  itemDate: string;
  snippet: string;
  mark: string;
  empty: string;
  loading: string;
  avatar: InitialsAvatarClassNames;
};

export type RoomMessageFindPanelProps = {
  classNames: RoomMessageFindPanelClassNames;
  labels: RoomMessageFindPanelLabels;
  query: string;
  onQueryChange: (value: string) => void;
  onClear: () => void;
  onClose: () => void;
  results: readonly RoomMessageFindResult[];
  loading?: boolean;
  onSelectResult?: (messageId: string) => void;
  className?: string;
  footer?: ReactNode;
};

export function roomMessageFindPanelBemClasses(
  prefix: string,
): RoomMessageFindPanelClassNames {
  const base = `${prefix}-room-message-find`;
  const ui = "delpi-ui-room-message-find";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    header: pair(`${base}__header`, `${ui}__header`),
    title: pair(`${base}__title`, `${ui}__title`),
    close: pair(`${base}__close`, `${ui}__close`),
    searchRow: pair(`${base}__search`, `${ui}__search`),
    input: pair(`${base}__input`, `${ui}__input`),
    clear: pair(`${base}__clear`, `${ui}__clear`),
    list: pair(`${base}__list`, `${ui}__list`),
    group: pair(`${base}__group`, `${ui}__group`),
    item: pair(`${base}__item`, `${ui}__item`),
    itemMeta: pair(`${base}__item-meta`, `${ui}__item-meta`),
    itemAuthorRow: pair(`${base}__item-author-row`, `${ui}__item-author-row`),
    itemAuthor: pair(`${base}__item-author`, `${ui}__item-author`),
    itemDate: pair(`${base}__item-date`, `${ui}__item-date`),
    snippet: pair(`${base}__snippet`, `${ui}__snippet`),
    mark: pair(`${base}__mark`, `${ui}__mark`),
    empty: pair(`${base}__empty`, `${ui}__empty`),
    loading: pair(`${base}__loading`, `${ui}__loading`),
    avatar: initialsAvatarBemClasses(prefix),
  };
}

export function RoomMessageFindPanel({
  classNames,
  labels,
  query,
  onQueryChange,
  onClear,
  onClose,
  results,
  loading = false,
  onSelectResult,
  className,
  footer,
}: RoomMessageFindPanelProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const q = query.trim();

  const grouped = (() => {
    const map = new Map<string, RoomMessageFindResult[]>();
    for (const row of results) {
      const key = (row.groupLabel || "").trim() || " ";
      const list = map.get(key) ?? [];
      list.push(row);
      map.set(key, list);
    }
    return [...map.entries()];
  })();

  return (
    <div className={rootClass}>
      <div className={classNames.header}>
        <h2 className={classNames.title}>{labels.title}</h2>
        <button
          type="button"
          className={classNames.close}
          aria-label={labels.closeAriaLabel}
          onClick={onClose}
        >
          <X size={16} aria-hidden />
        </button>
      </div>
      <div className={classNames.searchRow}>
        <Search size={16} aria-hidden />
        <input
          className={classNames.input}
          type="search"
          value={query}
          placeholder={labels.placeholder}
          aria-label={labels.placeholder}
          autoFocus
          onChange={(event) => onQueryChange(event.target.value)}
        />
        {q ? (
          <button
            type="button"
            className={classNames.clear}
            onClick={onClear}
          >
            {labels.clear}
          </button>
        ) : null}
      </div>
      {loading ? <p className={classNames.loading}>{labels.loading}</p> : null}
      {!loading && q && results.length === 0 ? (
        <p className={classNames.empty}>{labels.empty}</p>
      ) : null}
      {!loading && results.length > 0 ? (
        <div className={classNames.list}>
          {grouped.map(([group, rows]) => (
            <section key={group}>
              {group.trim() ? (
                <h3 className={classNames.group}>{group}</h3>
              ) : null}
              <ul>
                {rows.map((row) => {
                  const snippet = buildFindSnippet(row.bodyText, q);
                  const segments = splitFindHighlightSegments(snippet, q);
                  const avatarName =
                    row.authorAvatar?.name?.trim() || row.authorLabel;
                  return (
                    <li key={row.id}>
                      <button
                        type="button"
                        className={classNames.item}
                        onClick={() => onSelectResult?.(row.messageId)}
                      >
                        <div className={classNames.itemMeta}>
                          <span className={classNames.itemAuthorRow}>
                            <InitialsAvatar
                              classNames={classNames.avatar}
                              name={avatarName}
                              src={row.authorAvatar?.imageUrl}
                              size="sm"
                              previewable={false}
                            />
                            <span className={classNames.itemAuthor}>
                              {row.authorLabel}
                            </span>
                          </span>
                          {row.dateLabel ? (
                            <span className={classNames.itemDate}>
                              {row.dateLabel}
                            </span>
                          ) : null}
                        </div>
                        <p className={classNames.snippet}>
                          {segments.map((segment, index) =>
                            segment.match ? (
                              <mark key={index} className={classNames.mark}>
                                {segment.text}
                              </mark>
                            ) : (
                              <span key={index}>{segment.text}</span>
                            ),
                          )}
                        </p>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>
      ) : null}
      {footer}
    </div>
  );
}

export type DashboardRoomMessageFindPanelProps = Omit<
  RoomMessageFindPanelProps,
  "classNames"
>;

export function createDashboardRoomMessageFindPanel(prefix: string) {
  const classNames = roomMessageFindPanelBemClasses(prefix);
  return function DashboardRoomMessageFindPanel(
    props: DashboardRoomMessageFindPanelProps,
  ) {
    return <RoomMessageFindPanel classNames={classNames} {...props} />;
  };
}
