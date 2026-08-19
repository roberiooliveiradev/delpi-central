import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  InitialsAvatar,
  initialsAvatarBemClasses,
  type InitialsAvatarClassNames,
} from "../layout/InitialsAvatar";
import {
  MentionText,
  mentionTextBemClasses,
  type MentionTextClassNames,
  type MentionTextItem,
} from "./MentionText";

export type MessageThreadKind = "text" | "system" | "task_ref" | "pin" | string;

export type MessageThreadItem = {
  id: string;
  kind: MessageThreadKind;
  bodyText: string;
  createdAtLabel: string;
  authorName?: string | null;
  authorUserId?: string | null;
  parentId?: string | null;
  mentions?: MentionTextItem[];
  deleted?: boolean;
  mine?: boolean;
  /** Content under the body (reactions, unfurl, attachments). */
  belowBody?: ReactNode;
};

export type MessageThreadAction = {
  id: string;
  label: string;
  onClick: () => void;
  danger?: boolean;
  title?: string;
  icon?: ReactNode;
};

export type MessageThreadClassNames = {
  root: string;
  list: string;
  item: string;
  itemReply: string;
  itemMine: string;
  row: string;
  cluster: string;
  avatar: InitialsAvatarClassNames;
  system: string;
  bubble: string;
  bubbleMine: string;
  meta: string;
  author: string;
  time: string;
  body: string;
  actions: string;
  action: string;
  actionDanger: string;
  empty: string;
  mention: MentionTextClassNames;
};

export type MessageThreadProps = {
  messages: readonly MessageThreadItem[];
  classNames: MessageThreadClassNames;
  listAriaLabel: string;
  emptyLabel: string;
  /** Host builds edit/delete/reply/pin/task actions per message. */
  resolveActions?: (message: MessageThreadItem) => MessageThreadAction[];
  /** Override body render (default: MentionText). */
  renderBody?: (message: MessageThreadItem) => ReactNode;
  onMentionActivate?: MentionTextPropsOnActivate;
  className?: string;
};

type MentionTextPropsOnActivate = NonNullable<
  import("./MentionText").MentionTextProps["onMentionActivate"]
>;

export function messageThreadBemClasses(prefix: string): MessageThreadClassNames {
  const base = `${prefix}-message-thread`;
  const ui = "delpi-ui-message-thread";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    list: pair(`${base}__list`, `${ui}__list`),
    item: pair(`${base}__item`, `${ui}__item`),
    itemReply: pair(
      `${base}__item ${base}__item--reply`,
      `${ui}__item ${ui}__item--reply`,
    ),
    itemMine: pair(
      `${base}__item ${base}__item--mine`,
      `${ui}__item ${ui}__item--mine`,
    ),
    row: pair(`${base}__row`, `${ui}__row`),
    cluster: pair(`${base}__cluster`, `${ui}__cluster`),
    avatar: initialsAvatarBemClasses(prefix),
    system: pair(`${base}__system`, `${ui}__system`),
    bubble: pair(`${base}__bubble`, `${ui}__bubble`),
    bubbleMine: pair(
      `${base}__bubble ${base}__bubble--mine`,
      `${ui}__bubble ${ui}__bubble--mine`,
    ),
    meta: pair(`${base}__meta`, `${ui}__meta`),
    author: pair(`${base}__author`, `${ui}__author`),
    time: pair(`${base}__time`, `${ui}__time`),
    body: pair(`${base}__body`, `${ui}__body`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
    action: pair(`${base}__action`, `${ui}__action`),
    actionDanger: pair(
      `${base}__action ${base}__action--danger`,
      `${ui}__action ${ui}__action--danger`,
    ),
    empty: pair(`${base}__empty`, `${ui}__empty`),
    mention: mentionTextBemClasses(prefix),
  };
}

function isSystemKind(kind: MessageThreadKind): boolean {
  return kind === "system" || kind === "task_ref" || kind === "pin";
}

function itemClassName(
  classNames: MessageThreadClassNames,
  message: MessageThreadItem,
): string {
  const parts = [classNames.item];
  if (message.parentId) parts.push(classNames.itemReply);
  if (message.mine && !isSystemKind(message.kind)) parts.push(classNames.itemMine);
  return parts.join(" ");
}

/**
 * Message list with bubbles, system lines, and reply indent.
 * Action labels and body formatting policy live in the host.
 */
export function MessageThread({
  messages,
  classNames,
  listAriaLabel,
  emptyLabel,
  resolveActions,
  renderBody,
  onMentionActivate,
  className,
}: MessageThreadProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  if (messages.length === 0) {
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
        {messages.map((message) => {
          if (isSystemKind(message.kind)) {
            return (
              <li
                key={message.id}
                className={itemClassName(classNames, message)}
                data-message-id={message.id}
              >
                <div className={classNames.system} data-message-kind={message.kind}>
                  <span className={classNames.body}>{message.bodyText}</span>
                  {message.createdAtLabel ? (
                    <time className={classNames.time}>{message.createdAtLabel}</time>
                  ) : null}
                </div>
              </li>
            );
          }

          const actions = resolveActions?.(message) ?? [];
          const body =
            renderBody?.(message) ??
            (message.deleted ? (
              <span className={classNames.body}>{message.bodyText}</span>
            ) : (
              <MentionText
                classNames={classNames.mention}
                className={classNames.body}
                text={message.bodyText}
                mentions={message.mentions}
                onMentionActivate={onMentionActivate}
              />
            ));
          const avatarName = (message.authorName ?? "").trim();
          const avatar = avatarName ? (
            <InitialsAvatar
              classNames={classNames.avatar}
              name={avatarName}
              colorKey={message.authorUserId ?? avatarName}
              size="sm"
              previewable={false}
            />
          ) : null;

          const showAuthor = Boolean(message.authorName && !message.mine && !avatar);

          return (
            <li
              key={message.id}
              className={itemClassName(classNames, message)}
              data-message-id={message.id}
              data-message-kind={message.kind}
            >
              <div className={classNames.row}>
                {message.mine ? null : avatar}
                <div className={classNames.cluster}>
                  {actions.length > 0 ? (
                    <div className={classNames.actions}>
                      {actions.map((action) => (
                        <button
                          key={action.id}
                          type="button"
                          className={
                            action.danger ? classNames.actionDanger : classNames.action
                          }
                          aria-label={action.label}
                          title={action.title ?? action.label}
                          onClick={action.onClick}
                        >
                          {action.icon ?? action.label}
                        </button>
                      ))}
                    </div>
                  ) : null}
                  <article
                    className={message.mine ? classNames.bubbleMine : classNames.bubble}
                  >
                    {showAuthor ? (
                      <header className={classNames.meta}>
                        <span className={classNames.author}>{message.authorName}</span>
                      </header>
                    ) : null}
                    {body}
                    {message.belowBody}
                    {message.createdAtLabel ? (
                      <footer className={classNames.meta}>
                        <time className={classNames.time}>{message.createdAtLabel}</time>
                      </footer>
                    ) : null}
                  </article>
                </div>
                {message.mine ? avatar : null}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export type DashboardMessageThreadProps = Omit<MessageThreadProps, "classNames">;

export function createDashboardMessageThread(prefix: string) {
  const classNames = messageThreadBemClasses(prefix);
  return function DashboardMessageThread(props: DashboardMessageThreadProps) {
    return <MessageThread classNames={classNames} {...props} />;
  };
}
