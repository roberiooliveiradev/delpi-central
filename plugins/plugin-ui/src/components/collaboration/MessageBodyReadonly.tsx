import type { ReactNode } from "react";

import type { ResolveAttachmentImageSrc } from "../rich-text/richTextMarkdown";
import { MentionText, type MentionTextPropsOnActivate } from "./MentionText";
import { messageThreadBemClasses } from "./MessageThread";
import {
  messageBodyHtmlFromMarkdown,
  messageBodyHtmlIsPlainParagraph,
} from "./messageThreadMarkdown";
import type { MentionTextItem } from "./parseMentionText";

export type MessageBodyReadonlyProps = {
  markdown: string;
  mentions?: readonly MentionTextItem[] | null;
  className?: string;
  /** Prefixo BEM; default reutiliza tokens da bolha da thread. */
  bemPrefix?: string;
  resolveAttachmentImageSrc?: ResolveAttachmentImageSrc;
  onAttachmentImageClick?: (attachmentId: string) => void;
  onMentionActivate?: MentionTextPropsOnActivate;
};

/**
 * Corpo readonly de mensagem/tarefa — markdown sanitizado + chips @ + imagens attachment:
 */
export function MessageBodyReadonly({
  markdown,
  mentions,
  className,
  bemPrefix = "delpi-ui-message-thread",
  resolveAttachmentImageSrc,
  onAttachmentImageClick,
  onMentionActivate,
}: MessageBodyReadonlyProps): ReactNode {
  const classNames = messageThreadBemClasses(bemPrefix);
  const source = String(markdown ?? "").trim();
  if (!source) return null;

  const html = messageBodyHtmlFromMarkdown(
    source,
    mentions,
    classNames.mention.chip,
    { resolveAttachmentImageSrc },
  );

  if (!html || messageBodyHtmlIsPlainParagraph(html)) {
    return (
      <MentionText
        classNames={classNames.mention}
        className={[classNames.body, className].filter(Boolean).join(" ")}
        text={source}
        mentions={mentions ?? undefined}
        onMentionActivate={onMentionActivate}
      />
    );
  }

  return (
    <div
      className={[classNames.bodyRich, className].filter(Boolean).join(" ")}
      dangerouslySetInnerHTML={{ __html: html }}
      onClick={(event) => {
        if (!onAttachmentImageClick) return;
        const target = event.target as HTMLElement | null;
        const img = target?.closest?.("img[data-attachment-id]") as HTMLElement | null;
        const id = img?.getAttribute("data-attachment-id")?.trim();
        if (id) onAttachmentImageClick(id);
      }}
      role="presentation"
    />
  );
}

export type { MentionTextItem };
