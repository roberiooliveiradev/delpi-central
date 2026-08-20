/**
 * Markdown ↔ HTML for collaboration composer / message bubble (GFM subset).
 * Chat persistence = markdown in `body_text`; these helpers convert at the
 * composer submit edge and the MessageThread render edge (deck editor may
 * still store HTML separately).
 */
import { marked } from "marked";
import TurndownService from "turndown";
import { gfm } from "turndown-plugin-gfm";

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
  return html || "<p></p>";
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
