/**
 * Markdown ↔ HTML for RichTextEditor (GFM subset).
 * Storage remains HTML; these helpers only convert at the editor edge.
 */
import { marked } from "marked";
import TurndownService from "turndown";
import { gfm } from "turndown-plugin-gfm";

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
  return /<(?:p|div|table|ul|ol|li|h[1-6]|b|i|strong|em|a|blockquote|pre|code|tr|td|th)\b/i.test(
    stripped,
  );
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
    return turndown.turndown(source).trim();
  } catch {
    return "";
  }
}
