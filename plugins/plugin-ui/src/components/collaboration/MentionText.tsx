import type { ElementType, MouseEvent, MouseEventHandler, ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import { InitialsAvatar, initialsAvatarBemClasses } from "../layout/InitialsAvatar";
import { isSafeNavigationHref } from "../layout/PagePath";
import { shouldHandleInlineNavClick } from "../navigation/InlineNavLink";
import {
  parseMentionText,
  type MentionTextItem,
  type MentionTextSegment,
} from "./parseMentionText";

export type MentionTextClassNames = {
  root: string;
  chip: string;
  chipAvatar: string;
};

export type MentionTextProps = {
  text: string;
  /** Structured mentions from the host (kinds/labels); optional bare `@` still highlights. */
  mentions?: MentionTextItem[];
  classNames: MentionTextClassNames;
  className?: string;
  as?: "span" | "p" | "div";
  onMentionActivate?: (item: MentionTextItem, event: MouseEvent<HTMLElement>) => void;
};

const MENTION_AVATAR_CLASSES = initialsAvatarBemClasses("delpi-ui-mention");

export function mentionTextBemClasses(prefix: string): MentionTextClassNames {
  return {
    root: delpiUiClass(`${prefix}-mention-text`, "delpi-ui-mention-text"),
    chip: delpiUiClass(`${prefix}-mention-text__chip`, "delpi-ui-mention-text__chip"),
    chipAvatar: delpiUiClass(
      `${prefix}-mention-text__chip-avatar`,
      "delpi-ui-mention-text__chip-avatar",
    ),
  };
}

function displayLabel(value: string): string {
  const trimmed = value.trim();
  if (trimmed.startsWith("@")) return trimmed.slice(1) || trimmed;
  return trimmed;
}

function resolveHref(item: MentionTextItem | undefined): string | null {
  const href = (item?.href ?? "").trim();
  if (!href) return null;
  return isSafeNavigationHref(href) ? href : null;
}

function resolveAvatarName(item: MentionTextItem | undefined, shown: string): string {
  const fromItem = (item?.avatarName ?? "").trim();
  if (fromItem) return fromItem;
  return shown;
}

function hasAvatarChrome(item: MentionTextItem | undefined): boolean {
  if (!item) return false;
  return Boolean((item.avatarSrc ?? "").trim() || (item.avatarName ?? "").trim());
}

function renderChipAvatar(
  item: MentionTextItem | undefined,
  shown: string,
  chipAvatarClass: string,
): ReactNode {
  if (!hasAvatarChrome(item)) return null;
  const name = resolveAvatarName(item, shown);
  const src = (item?.avatarSrc ?? "").trim() || null;
  return (
    <InitialsAvatar
      name={name}
      src={src}
      size="sm"
      previewable={false}
      classNames={MENTION_AVATAR_CLASSES}
      className={chipAvatarClass}
    />
  );
}

/**
 * Renders message body with mention chips. Labels/kinds come from the consumer;
 * the kit only parses `@` and applies chrome.
 */
export function MentionText({
  text,
  mentions,
  classNames,
  className,
  as = "span",
  onMentionActivate,
}: MentionTextProps) {
  const Root = as as ElementType;
  const segments = parseMentionText(text, mentions);
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <Root className={rootClass}>
      {segments.map((segment, index) =>
        renderSegment(segment, index, classNames, onMentionActivate),
      )}
    </Root>
  );
}

function renderSegment(
  segment: MentionTextSegment,
  index: number,
  classNames: MentionTextClassNames,
  onMentionActivate: MentionTextProps["onMentionActivate"],
) {
  if (segment.type === "text") {
    return <span key={`t-${index}`}>{segment.value}</span>;
  }

  const item = segment.item;
  const href = resolveHref(item);
  const title = (item?.title ?? item?.label ?? segment.value).trim();
  const shown = displayLabel(segment.value);
  const ariaLabel = (item?.title ?? "").trim() || shown;
  const canActivate = Boolean(item && (href || onMentionActivate));
  const withAvatar = hasAvatarChrome(item);
  const chipClass = [
    canActivate ? withBemModifier(classNames.chip, "interactive") : classNames.chip,
    withAvatar ? withBemModifier(classNames.chip, "with-avatar") : null,
  ]
    .filter(Boolean)
    .join(" ");
  const avatar = renderChipAvatar(item, shown, classNames.chipAvatar);
  const label = <span className="delpi-ui-mention-text__chip-label">{shown}</span>;

  if (href && item) {
    const onClick: MouseEventHandler<HTMLAnchorElement> = (event) => {
      if (!shouldHandleInlineNavClick(event)) return;
      if (!onMentionActivate) return;
      event.preventDefault();
      onMentionActivate(item, event);
    };
    return (
      <a
        key={`m-${index}`}
        className={chipClass}
        href={href}
        title={title || undefined}
        aria-label={ariaLabel}
        data-mention-kind={item.kind || undefined}
        onClick={onMentionActivate ? onClick : undefined}
      >
        {avatar}
        {label}
      </a>
    );
  }

  if (item && onMentionActivate) {
    return (
      <button
        key={`m-${index}`}
        type="button"
        className={chipClass}
        title={title || undefined}
        aria-label={ariaLabel}
        data-mention-kind={item.kind || undefined}
        onClick={(event) => onMentionActivate(item, event)}
      >
        {avatar}
        {label}
      </button>
    );
  }

  return (
    <span
      key={`m-${index}`}
      className={chipClass}
      data-mention-kind={item?.kind || undefined}
    >
      {avatar}
      {label}
    </span>
  );
}

export type DashboardMentionTextProps = Omit<MentionTextProps, "classNames">;

export function createDashboardMentionText(prefix: string) {
  const classNames = mentionTextBemClasses(prefix);
  return function DashboardMentionText(props: DashboardMentionTextProps) {
    return <MentionText classNames={classNames} {...props} />;
  };
}

export type { MentionTextItem, MentionTextSegment };
