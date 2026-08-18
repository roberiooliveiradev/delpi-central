import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
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
  /** Content under the body (reactions, unfurl, attachments). */
  belowBody?: ReactNode;
};

export type MessageThreadAction = {
  id: string;
  label: string;
  onClick: () => void;
  danger?: boolean;
};

export type MessageThreadClassNames = {
  root: string;
  list: string;
  item: string;
  itemReply: string;
  system: string;
  bubble: string;
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
    system: pair(`${base}__system`, `${ui}__system`),
    bubble: pair(`${base}__bubble`, `${ui}__bubble`),
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
          const isReply = Boolean(message.parentId);
          const itemClass = isReply ? classNames.itemReply : classNames.item;
          if (message.kind === "system") {
            return (
              <li key={message.id} className={itemClass}>
                <div className={classNames.system} data-message-kind="system">
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

          return (
            <li key={message.id} className={itemClass} data-message-kind={message.kind}>
              <article className={classNames.bubble}>
                <header className={classNames.meta}>
                  {message.authorName ? (
                    <span className={classNames.author}>{message.authorName}</span>
                  ) : null}
                  {message.createdAtLabel ? (
                    <time className={classNames.time}>{message.createdAtLabel}</time>
                  ) : null}
                </header>
                {body}
                {actions.length > 0 ? (
                  <div className={classNames.actions}>
                    {actions.map((action) => (
                      <button
                        key={action.id}
                        type="button"
                        className={action.danger ? classNames.actionDanger : classNames.action}
                        onClick={action.onClick}
                      >
                        {action.label}
                      </button>
                    ))}
                  </div>
                ) : null}
                {message.belowBody}
              </article>
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
