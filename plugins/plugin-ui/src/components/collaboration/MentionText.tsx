import type { ElementType, MouseEvent, MouseEventHandler } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
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

export function mentionTextBemClasses(prefix: string): MentionTextClassNames {
  return {
    root: delpiUiClass(`${prefix}-mention-text`, "delpi-ui-mention-text"),
    chip: delpiUiClass(`${prefix}-mention-text__chip`, "delpi-ui-mention-text__chip"),
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
  const canActivate = Boolean(item && (href || onMentionActivate));
  const chipClass = canActivate
    ? withBemModifier(classNames.chip, "interactive")
    : classNames.chip;

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
        data-mention-kind={item.kind || undefined}
        onClick={onMentionActivate ? onClick : undefined}
      >
        {shown}
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
        data-mention-kind={item.kind || undefined}
        onClick={(event) => onMentionActivate(item, event)}
      >
        {shown}
      </button>
    );
  }

  return (
    <span
      key={`m-${index}`}
      className={chipClass}
      data-mention-kind={item?.kind || undefined}
    >
      {shown}
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
