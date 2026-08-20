/**
 * Markdown ↔ HTML for collaboration composer / message bubble (GFM subset).
 * Chat persistence = markdown in `body_text`; these helpers convert at the
 * composer submit edge and the MessageThread render edge (deck editor may
 * still store HTML separately).
 */
import { marked } from "marked";
import TurndownService from "turndown";
import { gfm } from "turndown-plugin-gfm";

import { parseAlignFromImageTitle } from "../collaboration/mentionComposerInlineImage";
import { readInlineFontSizePx } from "./richTextHtmlFormat";

marked.setOptions({
  gfm: true,
  breaks: false,
});

const turndown = new TurndownService({
  headingStyle: "atx",
  codeBlockStyle: "fenced",
  bulletListMarker: "-",
  emDelimiter: "*",
  strongDelimiter: "**",
});
turndown.use(gfm);

turndown.addRule("inlineFontSize", {
  filter: (node) =>
    node.nodeName === "SPAN" && Boolean(readInlineFontSizePx(node as Element)),
  replacement: (content, node) => {
    const px = readInlineFontSizePx(node as Element);
    if (!px) return content;
    return `<span style="font-size:${px}px">${content}</span>`;
  },
});

/** Sublinhado não tem marcador GFM — persiste como HTML inline no markdown. */
turndown.addRule("underline", {
  filter: (node) => node.nodeName === "U",
  replacement: (content) => `<u>${content}</u>`,
});

/** Parágrafo com text-align ≠ left — HTML island (mesmo padrão underline/font-size). */
turndown.addRule("paragraphTextAlign", {
  filter: (node) => {
    if (node.nodeName !== "P") return false;
    const align = String((node as HTMLElement).style?.textAlign || "")
      .trim()
      .toLowerCase();
    return Boolean(align) && align !== "left" && align !== "start";
  },
  replacement: (content, node) => {
    const align = String((node as HTMLElement).style.textAlign || "")
      .trim()
      .toLowerCase();
    if (!align || align === "left" || align === "start") return content;
    return `\n\n<p style="text-align:${align}">${content}</p>\n\n`;
  },
});

/**
 * Fence estável para `<pre><code>` (e `<pre>` já normalizado).
 * Garante backticks mesmo se o plugin GFM falhar em edge cases.
 */
turndown.addRule("fencedCodeBlock", {
  filter: (node) => {
    if (node.nodeName !== "PRE") return false;
    const el = node as HTMLElement;
    const code = el.querySelector(":scope > code");
    return Boolean(code) || Boolean((el.textContent ?? "").trim());
  },
  replacement: (_content, node) => {
    const el = node as HTMLElement;
    const code = el.querySelector(":scope > code");
    const raw = (code?.textContent ?? el.textContent ?? "").replace(/\n$/, "");
    return `\n\n\`\`\`\n${raw}\n\`\`\`\n\n`;
  },
});

/** Sala: `![alt](attachment:…)` / pending — inline no parágrafo; sem title de align. */
turndown.addRule("attachmentInlineImage", {
  filter: (node) => {
    if (node.nodeName === "IMG") {
      const el = node as HTMLElement;
      const href = el.getAttribute("data-attachment-href") || "";
      return (
        Boolean(el.getAttribute("data-attachment-pending")) ||
        href.startsWith("attachment:")
      );
    }
    if (node.nodeName === "FIGURE" || node.nodeName === "SPAN") {
      return Boolean(
        (node as Element).querySelector(
          "img[data-attachment-pending], img[data-attachment-href^='attachment:']",
        ),
      );
    }
    return false;
  },
  replacement: (_content, node) => {
    const root = node as HTMLElement;
    const img =
      root.nodeName === "IMG"
        ? root
        : (root.querySelector("img") as HTMLElement | null);
    if (!img) return "";
    const pending = img.getAttribute("data-attachment-pending") || "";
    const id = img.getAttribute("data-attachment-id") || "";
    const href =
      img.getAttribute("data-attachment-href") ||
      (pending
        ? `attachment:pending:${pending}`
        : id
          ? `attachment:${id}`
          : "");
    if (!href.startsWith("attachment:")) return "";
    const alt = (img.getAttribute("alt") || "").replace(/[[\]]/g, "");
    return `![${alt}](${href})`;
  },
});

const MD_LINE_HINT =
  /^(#{1,6}\s|[-*+]\s|\d+\.\s|>\s|```|~~~|\|.+\||-{3,}|\*{3,}|_{3,})/;
const MD_INLINE_HINT = /(\*\*[^*\n]+\*\*|__[^_\n]+__|`[^`\n]+`|\[[^\]]+\]\([^)]+\))/;

/**
 * Conservative: true when plain text looks like Markdown, not prose alone.
 * Avoids treating normal paragraphs as MD on paste.
 */
export function clipboardLooksLikeMarkdown(text: string): boolean {
  const raw = (text || "").replace(/\r\n/g, "\n").trim();
  if (!raw) return false;
  if (/^\s*</.test(raw) && /<\/[a-z][\w:-]*>/i.test(raw)) return false;

  const lines = raw.split("\n").map((line) => line.trimEnd());
  let score = 0;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    if (MD_LINE_HINT.test(trimmed)) score += 2;
    else if (/\*\*[^*\n]+\*\*|__[^_\n]+__/.test(trimmed)) score += 2;
    else if (MD_INLINE_HINT.test(trimmed)) score += 1;
  }
  if (/```[\s\S]*```/.test(raw) || /~~~[\s\S]*~~~/.test(raw)) score += 3;
  return score >= 2;
}

/** True when clipboard HTML carries real rich structure (not a plain-text wrapper). */
export function clipboardHasUsefulHtml(html: string | undefined | null): boolean {
  if (!html?.trim()) return false;
  const stripped = html
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/<\/?(?:html|body|head|meta|fragment|span)(?:\s[^>]*)?>/gi, " ")
    .replace(/<br\s*\/?>/gi, " ")
    .trim();
  return /<(?:p|div|table|ul|ol|li|h[1-6]|b|i|strong|em|u|s|a|blockquote|pre|code|tr|td|th)\b/i.test(
    stripped,
  );
}

const BLOCK_BREAK_TAGS = new Set(["DIV", "P", "LI"]);

/**
 * Flatten contenteditable artifacts inside a code host so Turndown sees real `\n`.
 * Replaces `<br>` and block wrappers with text newlines; unwraps nested inlines.
 */
function flattenCodeHostContent(host: Element, ownerDoc: Document): void {
  const walk = (parent: Node) => {
    const children = Array.from(parent.childNodes);
    for (const child of children) {
      if (child.nodeType === Node.ELEMENT_NODE) {
        const el = child as Element;
        const tag = el.tagName;
        if (tag === "BR") {
          parent.replaceChild(ownerDoc.createTextNode("\n"), el);
          continue;
        }
        if (BLOCK_BREAK_TAGS.has(tag)) {
          walk(el);
          const frag = ownerDoc.createDocumentFragment();
          while (el.firstChild) frag.appendChild(el.firstChild);
          frag.appendChild(ownerDoc.createTextNode("\n"));
          parent.replaceChild(frag, el);
          continue;
        }
        // Unwrap other wrappers inside code (span, font, etc.) keeping text.
        if (tag !== "CODE") {
          walk(el);
          const frag = ownerDoc.createDocumentFragment();
          while (el.firstChild) frag.appendChild(el.firstChild);
          parent.replaceChild(frag, el);
          continue;
        }
        walk(el);
      }
    }
  };
  walk(host);
}

/**
 * Prepara HTML do contenteditable para Turndown estável (chat composer).
 * - `pre` sem `code` → envolve em `<code>`
 * - `<br>` / `div` / `p` dentro de `pre`/`code` → `\n` textuais
 */
export function normalizeRichTextHtmlForMarkdown(html: string): string {
  const source = (html ?? "").trim();
  if (!source || typeof DOMParser === "undefined") return source;
  try {
    const doc = new DOMParser().parseFromString(
      `<div id="__md_root">${source}</div>`,
      "text/html",
    );
    const root = doc.getElementById("__md_root");
    if (!root) return source;

    for (const pre of Array.from(root.querySelectorAll("pre"))) {
      let code = pre.querySelector(":scope > code");
      if (!code) {
        code = doc.createElement("code");
        while (pre.firstChild) code.appendChild(pre.firstChild);
        pre.appendChild(code);
      }
      flattenCodeHostContent(code, doc);
    }

    // Inline `<code>` com <br> (raro) também.
    for (const code of Array.from(root.querySelectorAll("code"))) {
      if (code.parentElement?.tagName === "PRE") continue;
      if (code.querySelector("br, div, p")) flattenCodeHostContent(code, doc);
    }

    return root.innerHTML;
  } catch {
    return source;
  }
}

export function markdownToRichTextHtml(markdown: string): string {
  const source = (markdown ?? "").trim();
  if (!source) return "<p></p>";
  const parsed = marked.parse(source, { async: false });
  const html = typeof parsed === "string" ? parsed.trim() : "";
  if (!html) return "<p></p>";
  return enhanceAttachmentImagesInHtml(html);
}

/** Marca `<img src="attachment:…">` do marked com data attrs para o composer/bolha. */
export function enhanceAttachmentImagesInHtml(html: string): string {
  if (!html.includes("attachment:")) return html;
  try {
    const doc = new DOMParser().parseFromString(`<div id="root">${html}</div>`, "text/html");
    const root = doc.getElementById("root");
    if (!root) return html;
    for (const img of Array.from(root.querySelectorAll("img"))) {
      const src = (img.getAttribute("src") || "").trim();
      if (src.startsWith("blob:") || src.startsWith("data:")) continue;
      if (!src.startsWith("attachment:")) continue;
      img.setAttribute("data-attachment-href", src);
      if (src.startsWith("attachment:pending:")) {
        img.setAttribute("data-attachment-pending", src.slice("attachment:pending:".length));
      } else {
        img.setAttribute(
          "data-attachment-id",
          src.slice("attachment:".length),
        );
      }
      const title = img.getAttribute("title") || "";
      const align = parseAlignFromImageTitle(title);
      if (title) img.removeAttribute("title");
      img.removeAttribute("src");

      const wrapper = doc.createElement("span");
      wrapper.className =
        "delpi-ui-mention-composer__inline-image delpi-ui-message-thread__inline-image";
      wrapper.setAttribute("contenteditable", "false");
      img.parentNode?.insertBefore(wrapper, img);
      wrapper.appendChild(img);

      // Legacy markdown title `"align=…"` → paragraph text-align (Word model).
      const parent = wrapper.parentElement;
      if (parent && parent.tagName === "P" && align !== "left") {
        parent.style.textAlign = align;
      }

      const btn = doc.createElement("button");
      btn.type = "button";
      btn.className = "delpi-ui-mention-composer__inline-image-remove";
      btn.setAttribute("data-inline-image-remove", "1");
      btn.setAttribute("contenteditable", "false");
      btn.setAttribute("tabindex", "-1");
      const alt = img.getAttribute("alt") || "image";
      btn.setAttribute("aria-label", `Remove ${alt}`);
      btn.textContent = "×";
      wrapper.appendChild(btn);
    }
    return root.innerHTML;
  } catch {
    return html;
  }
}

export type ResolveAttachmentImageSrc = (
  attachmentId: string,
) => string | null | undefined;

/** Resolve `src` for `<img data-attachment-id|data-attachment-pending>` (bubble + composer). */
export function applyAttachmentImageSources(
  html: string,
  resolve?: ResolveAttachmentImageSrc,
): string {
  if (
    !resolve ||
    (!html.includes("data-attachment-id") && !html.includes("data-attachment-pending"))
  ) {
    return html;
  }
  if (typeof DOMParser === "undefined") return html;
  try {
    const doc = new DOMParser().parseFromString(
      `<div id="__att_root">${html}</div>`,
      "text/html",
    );
    const root = doc.getElementById("__att_root");
    if (!root) return html;
    const imgs = root.querySelectorAll(
      "img[data-attachment-id], img[data-attachment-pending]",
    );
    for (const img of Array.from(imgs)) {
      const id =
        img.getAttribute("data-attachment-id") ||
        img.getAttribute("data-attachment-pending") ||
        "";
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

export function richTextHtmlToMarkdown(html: string): string {
  const source = (html ?? "").trim();
  if (!source || source === "<p></p>") return "";
  try {
    const normalized = normalizeRichTextHtmlForMarkdown(source);
    return turndown.turndown(normalized).trim();
  } catch {
    return "";
  }
}
