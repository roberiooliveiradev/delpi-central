import { markdownToRichTextHtml } from "../rich-text/richTextMarkdown";
import { stripDangerousRichTextTags } from "../rich-text/richTextHtmlFormat";
import {
  parseMentionText,
  type MentionTextItem,
} from "./parseMentionText";

/**
 * Preview de inbox: remove marcadores markdown comuns e colapsa whitespace.
 * Não interpreta HTML — só texto plano.
 */
export function markdownToPlainPreview(markdown: string, maxLength = 160): string {
  let text = String(markdown ?? "").replace(/\r\n/g, "\n");
  if (!text.trim()) return "";

  text = text.replace(/```[\s\S]*?```/g, " ");
  text = text.replace(/`([^`]+)`/g, "$1");
  text = text.replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1");
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  text = text.replace(/^#{1,6}\s+/gm, "");
  text = text.replace(/^>\s?/gm, "");
  text = text.replace(/^[-*+]\s+/gm, "");
  text = text.replace(/^\d+\.\s+/gm, "");
  text = text.replace(/(\*\*|__)(.*?)\1/g, "$2");
  text = text.replace(/(\*|_)(.*?)\1/g, "$2");
  text = text.replace(/~~(.*?)~~/g, "$1");
  text = text.replace(/<\/?u>/gi, "");
  text = text.replace(/<span\b[^>]*>|<\/span>/gi, "");
  text = text.replace(/\s+/g, " ").trim();

  if (maxLength > 0 && text.length > maxLength) {
    const cut = text.slice(0, maxLength - 1);
    const trimmed = cut.replace(/\s+\S*$/, "").trimEnd() || cut.trimEnd();
    return `${trimmed}…`;
  }
  return text;
}

function displayMentionLabel(value: string): string {
  const trimmed = value.trim();
  if (trimmed.startsWith("@")) return trimmed.slice(1) || trimmed;
  return trimmed;
}

/**
 * HTML sanitizado a partir do markdown persistido em `body_text`.
 * Menções viram chips (span) — unfurl/clique ficam no host via belowBody / plain path.
 */
export type MessageBodyHtmlOptions = {
  resolveAttachmentImageSrc?: (attachmentId: string) => string | null | undefined;
};

/** UUIDs em `![…](attachment:{uuid})` — ignora `pending:`. */
export function attachmentIdsInMarkdown(markdown: string): string[] {
  const text = String(markdown ?? "");
  const re = /!\[[^\]]*]\(attachment:(?!pending:)([^)\s]+)\)/g;
  const seen = new Set<string>();
  const ids: string[] = [];
  let match: RegExpExecArray | null;
  while ((match = re.exec(text))) {
    const id = String(match[1] || "").trim();
    if (!id || seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  return ids;
}

export function messageBodyHtmlFromMarkdown(
  markdown: string,
  mentions?: readonly MentionTextItem[] | null,
  chipClassName = "delpi-ui-mention-text__chip",
  options?: MessageBodyHtmlOptions,
): string {
  const source = String(markdown ?? "").trim();
  if (!source) return "";
  const raw = markdownToRichTextHtml(source);
  const cleaned = stripDangerousRichTextTags(raw).trim();
  if (!cleaned) return "";
  const withSrc = applyAttachmentImageSources(cleaned, options?.resolveAttachmentImageSrc);
  return enrichMessageHtmlMentions(withSrc, mentions, chipClassName);
}

function applyAttachmentImageSources(
  html: string,
  resolve?: MessageBodyHtmlOptions["resolveAttachmentImageSrc"],
): string {
  if (!resolve || !html.includes("data-attachment-id")) return html;
  if (typeof DOMParser === "undefined") return html;
  try {
    const doc = new DOMParser().parseFromString(
      `<div id="__att_root">${html}</div>`,
      "text/html",
    );
    const root = doc.getElementById("__att_root");
    if (!root) return html;
    for (const img of Array.from(root.querySelectorAll("img[data-attachment-id]"))) {
      const id = img.getAttribute("data-attachment-id") || "";
      if (!id) continue;
      const src = resolve(id);
      if (src) {
        img.setAttribute("src", src);
        img.setAttribute("loading", "lazy");
      }
    }
    return root.innerHTML;
  } catch {
    return html;
  }
}

/** True when HTML is a single plain paragraph (prefer MentionText interativo). */
export function messageBodyHtmlIsPlainParagraph(html: string): boolean {
  const source = (html || "").trim();
  if (!source) return true;
  if (typeof DOMParser === "undefined") {
    return /^<p(?:\s[^>]*)?>[^<]*<\/p>$/i.test(source);
  }
  try {
    const doc = new DOMParser().parseFromString(
      `<div id="__mt_root">${source}</div>`,
      "text/html",
    );
    const root = doc.getElementById("__mt_root");
    if (!root) return false;
    const children = Array.from(root.childNodes).filter((node) => {
      if (node.nodeType === Node.TEXT_NODE) return Boolean(node.textContent?.trim());
      return node.nodeType === Node.ELEMENT_NODE;
    });
    if (children.length !== 1 || children[0]!.nodeType !== Node.ELEMENT_NODE) {
      return false;
    }
    const el = children[0] as Element;
    if (el.tagName.toLowerCase() !== "p") return false;
    return !el.querySelector(
      "a, code, pre, strong, b, em, i, u, s, del, ul, ol, blockquote, br, figure, img",
    );
  } catch {
    return false;
  }
}

export function enrichMessageHtmlMentions(
  html: string,
  mentions: readonly MentionTextItem[] | null | undefined,
  chipClassName: string,
): string {
  const raw = (html || "").trim();
  if (!raw || typeof DOMParser === "undefined") return raw;
  try {
    const doc = new DOMParser().parseFromString(
      `<div id="__mt_root">${raw}</div>`,
      "text/html",
    );
    const root = doc.getElementById("__mt_root");
    if (!root) return raw;

    const walker = doc.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const textNodes: Text[] = [];
    while (walker.nextNode()) {
      textNodes.push(walker.currentNode as Text);
    }

    for (const node of textNodes) {
      const parent = node.parentElement;
      if (!parent) continue;
      if (parent.closest("code, pre, a, script, style")) continue;
      const value = node.textContent ?? "";
      if (!value.includes("@")) continue;
      const segments = parseMentionText(value, mentions);
      if (segments.every((segment) => segment.type === "text")) continue;

      const frag = doc.createDocumentFragment();
      for (const segment of segments) {
        if (segment.type === "text") {
          frag.appendChild(doc.createTextNode(segment.value));
          continue;
        }
        const span = doc.createElement("span");
        span.className = chipClassName;
        span.textContent = displayMentionLabel(segment.value);
        if (segment.item?.kind) {
          span.setAttribute("data-mention-kind", segment.item.kind);
        }
        frag.appendChild(span);
      }
      parent.replaceChild(frag, node);
    }

    return root.innerHTML;
  } catch {
    return raw;
  }
}
