import type { MouseEventHandler, ReactNode } from "react";

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
import {
  messageBodyHtmlFromMarkdown,
  messageBodyHtmlIsPlainParagraph,
} from "./messageThreadMarkdown";

export type MessageThreadKind = "text" | "system" | "task_ref" | "pin" | string;

export type MessageThreadItem = {
  id: string;
  kind: MessageThreadKind;
  bodyText: string;
  createdAtLabel: string;
  authorName?: string | null;
  authorUserId?: string | null;
  /** Com `authorLinkTitle`, o avatar vira `<a href>` (mesmo contrato do InitialsAvatar). */
  authorHref?: string | null;
  /** Foto resolvida pelo consumidor (blob URL da plataforma). */
  authorSrc?: string | null;
  authorLinkTitle?: string | null;
  onAuthorNavigate?: MouseEventHandler<HTMLAnchorElement>;
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
  stack: string;
  itemContinue: string;
  avatar: InitialsAvatarClassNames;
  system: string;
  bubble: string;
  bubbleMine: string;
  meta: string;
  author: string;
  time: string;
  body: string;
  bodyRich: string;
  editSlot: string;
  itemEditing: string;
  actions: string;
  action: string;
  actionDanger: string;
  empty: string;
  mention: MentionTextClassNames;
  quote: string;
  quoteMeta: string;
  quoteAuthor: string;
  quoteTime: string;
  quoteBody: string;
};

export type MessageThreadProps = {
  messages: readonly MessageThreadItem[];
  classNames: MessageThreadClassNames;
  listAriaLabel: string;
  emptyLabel: string;
  /** Host builds edit/delete/reply/pin/task actions per message. */
  resolveActions?: (message: MessageThreadItem) => MessageThreadAction[];
  /** When set, that message shows `renderEditSlot` instead of the body. */
  editingId?: string | null;
  /** In-place composer (or other editor) while `editingId` matches. */
  renderEditSlot?: (message: MessageThreadItem) => ReactNode;
  /** Override body render (default: markdown sanitizado + MentionText no plano). */
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
    stack: pair(`${base}__stack`, `${ui}__stack`),
    itemContinue: pair(
      `${base}__item ${base}__item--continue`,
      `${ui}__item ${ui}__item--continue`,
    ),
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
    bodyRich: pair(
      `${base}__body ${base}__body--rich`,
      `${ui}__body ${ui}__body--rich`,
    ),
    editSlot: pair(`${base}__edit-slot`, `${ui}__edit-slot`),
    itemEditing: pair(
      `${base}__item ${base}__item--editing`,
      `${ui}__item ${ui}__item--editing`,
    ),
    actions: pair(`${base}__actions`, `${ui}__actions`),
    action: pair(`${base}__action`, `${ui}__action`),
    actionDanger: pair(
      `${base}__action ${base}__action--danger`,
      `${ui}__action ${ui}__action--danger`,
    ),
    empty: pair(`${base}__empty`, `${ui}__empty`),
    mention: mentionTextBemClasses(prefix),
    quote: pair(`${base}__quote`, `${ui}__quote`),
    quoteMeta: pair(`${base}__quote-meta`, `${ui}__quote-meta`),
    quoteAuthor: pair(`${base}__quote-author`, `${ui}__quote-author`),
    quoteTime: pair(`${base}__quote-time`, `${ui}__quote-time`),
    quoteBody: pair(`${base}__quote-body`, `${ui}__quote-body`),
  };
}

function isSystemKind(kind: MessageThreadKind): boolean {
  return kind === "system" || kind === "task_ref" || kind === "pin";
}

function sameAuthorRun(
  previous: MessageThreadItem | undefined,
  current: MessageThreadItem,
): boolean {
  if (!previous || isSystemKind(previous.kind) || isSystemKind(current.kind)) {
    return false;
  }
  if (Boolean(previous.mine) !== Boolean(current.mine)) return false;
  const previousKey = (previous.authorUserId ?? previous.authorName ?? "").trim();
  const currentKey = (current.authorUserId ?? current.authorName ?? "").trim();
  return previousKey.length > 0 && previousKey === currentKey;
}

function parentQuote(
  messages: readonly MessageThreadItem[],
  message: MessageThreadItem,
): MessageThreadItem | null {
  const parentId = (message.parentId ?? "").trim();
  if (!parentId) return null;
  const parent = messages.find((item) => item.id === parentId);
  if (!parent || isSystemKind(parent.kind)) return null;
  return parent;
}

function itemClassName(
  classNames: MessageThreadClassNames,
  message: MessageThreadItem,
  continues: boolean,
  editing: boolean,
): string {
  const parts = [classNames.item];
  if (message.parentId) parts.push(classNames.itemReply);
  if (continues) parts.push(classNames.itemContinue);
  if (message.mine && !isSystemKind(message.kind)) parts.push(classNames.itemMine);
  if (editing) parts.push(classNames.itemEditing);
  return parts.join(" ");
}

/**
 * Message list with bubbles, system lines, and reply indent.
 * Action labels and body formatting policy live in the host.
 */
function defaultMessageBody(
  message: MessageThreadItem,
  classNames: MessageThreadClassNames,
  onMentionActivate: MentionTextPropsOnActivate | undefined,
): ReactNode {
  if (message.deleted) {
    return <span className={classNames.body}>{message.bodyText}</span>;
  }

  const html = messageBodyHtmlFromMarkdown(
    message.bodyText,
    message.mentions,
    classNames.mention.chip,
  );

  if (!html || messageBodyHtmlIsPlainParagraph(html)) {
    return (
      <MentionText
        classNames={classNames.mention}
        className={classNames.body}
        text={message.bodyText}
        mentions={message.mentions}
        onMentionActivate={onMentionActivate}
      />
    );
  }

  return (
    <div
      className={classNames.bodyRich}
      // HTML já passou por stripDangerousRichTextTags + enrich de menções.
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

export function MessageThread({
  messages,
  classNames,
  listAriaLabel,
  emptyLabel,
  resolveActions,
  editingId = null,
  renderEditSlot,
  renderBody,
  onMentionActivate,
  className,
}: MessageThreadProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const activeEditingId = (editingId ?? "").trim();

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
        {messages.map((message, index) => {
          const continues = sameAuthorRun(messages[index - 1], message);
          const isEditing =
            Boolean(activeEditingId) &&
            message.id === activeEditingId &&
            Boolean(renderEditSlot);
          if (isSystemKind(message.kind)) {
            return (
              <li
                key={message.id}
                className={itemClassName(classNames, message, false, false)}
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

          const actions = isEditing ? [] : resolveActions?.(message) ?? [];
          const quoted = parentQuote(messages, message);
          const body = isEditing
            ? (
                <div className={classNames.editSlot}>
                  {renderEditSlot?.(message)}
                </div>
              )
            : (
                renderBody?.(message) ??
                defaultMessageBody(message, classNames, onMentionActivate)
              );
          const avatarName = (message.authorName ?? "").trim();
          const authorHref = (message.authorHref ?? "").trim();
          const authorLinkTitle = (message.authorLinkTitle ?? "").trim();
          const authorSrc = (message.authorSrc ?? "").trim() || null;
          const showAvatar = Boolean(avatarName && !message.mine && !continues);
          const avatar = showAvatar ? (
            authorHref && authorLinkTitle ? (
              <InitialsAvatar
                classNames={classNames.avatar}
                name={avatarName}
                colorKey={message.authorUserId ?? avatarName}
                size="sm"
                src={authorSrc}
                href={authorHref}
                title={authorLinkTitle}
                onNavigate={message.onAuthorNavigate}
              />
            ) : (
              <InitialsAvatar
                classNames={classNames.avatar}
                name={avatarName}
                colorKey={message.authorUserId ?? avatarName}
                size="sm"
                src={authorSrc}
                previewable={false}
              />
            )
          ) : null;
          const showAuthor = Boolean(avatarName && !message.mine && !continues);
          const showHeading = !continues && (showAuthor || Boolean(message.createdAtLabel));

          return (
            <li
              key={message.id}
              className={itemClassName(classNames, message, continues, isEditing)}
              data-message-id={message.id}
              data-message-kind={message.kind}
              data-editing={isEditing ? "true" : undefined}
            >
              <div className={classNames.row}>
                {avatar}
                <div className={classNames.cluster}>
                  {showHeading ? (
                    <header className={classNames.meta}>
                      {showAuthor ? (
                        <span className={classNames.author}>{message.authorName}</span>
                      ) : null}
                      {message.createdAtLabel ? (
                        <time className={classNames.time}>{message.createdAtLabel}</time>
                      ) : null}
                    </header>
                  ) : null}
                  <div className={classNames.stack}>
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
                      {quoted ? (
                        <blockquote className={classNames.quote}>
                          <header className={classNames.quoteMeta}>
                            {quoted.authorName ? (
                              <span className={classNames.quoteAuthor}>
                                {quoted.authorName}
                              </span>
                            ) : null}
                            {quoted.createdAtLabel ? (
                              <time className={classNames.quoteTime}>
                                {quoted.createdAtLabel}
                              </time>
                            ) : null}
                          </header>
                          <p className={classNames.quoteBody}>{quoted.bodyText}</p>
                        </blockquote>
                      ) : null}
                      {body}
                      {isEditing ? null : message.belowBody}
                    </article>
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

export type DashboardMessageThreadProps = Omit<MessageThreadProps, "classNames">;

export function createDashboardMessageThread(prefix: string) {
  const classNames = messageThreadBemClasses(prefix);
  return function DashboardMessageThread(props: DashboardMessageThreadProps) {
    return <MessageThread classNames={classNames} {...props} />;
  };
}
