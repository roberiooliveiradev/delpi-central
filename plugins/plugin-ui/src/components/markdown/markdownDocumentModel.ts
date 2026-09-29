/**
 * Document-grade Markdown model for article readers (GFM + code + Mermaid).
 *
 * Pure parsing/segmentation layer used by `MarkdownDocument`: turns a
 * canonical markdown source into render segments and a heading outline with
 * stable, deterministic anchor ids. `content_md` remains the single source —
 * this model is a derived read-only projection (no persistence).
 *
 * Security: markdown segments are rendered via `marked` (GFM) and sanitized
 * through the canonical `stripDangerousRichTextTags` — no raw HTML execution,
 * no `javascript:` URLs, no inline event handlers.
 */
import { marked, Renderer, type Token, type Tokens } from "marked";

import { stripDangerousRichTextTags } from "../rich-text/richTextHtmlFormat";

export type MarkdownDocumentSegment =
  | { type: "markdown"; html: string }
  | { type: "code"; lang: string; code: string }
  | { type: "mermaid"; code: string };

export type MarkdownDocumentOutlineItem = {
  id: string;
  depth: number;
  text: string;
};

export type MarkdownDocumentModel = {
  segments: MarkdownDocumentSegment[];
  /** Headings depth >= 2 (title-as-H1 is deduplicated before this). */
  outline: MarkdownDocumentOutlineItem[];
};

const MARKDOWN_PARSE_OPTIONS = { gfm: true, breaks: false } as const;
const MERMAID_LANG = "mermaid";

function plainTextFromInlineMarkdown(source: string): string {
  return String(source || "")
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/<[^>]*>/g, "")
    .replace(/[*_~`]+/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeComparableTitle(value: string): string {
  return plainTextFromInlineMarkdown(value).toLowerCase();
}

export function markdownHeadingSlug(text: string): string {
  const slug = plainTextFromInlineMarkdown(text)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/[\s-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug || "section";
}

/** Case/whitespace-safe: is the first block an H1 duplicating the doc title? */
export function isLeadingTitleDuplicate(
  markdown: string,
  documentTitle: string,
): boolean {
  const title = normalizeComparableTitle(documentTitle);
  if (!title) return false;
  const firstBlock = marked
    .lexer(String(markdown || ""), MARKDOWN_PARSE_OPTIONS)
    .find((token) => token.type !== "space");
  if (!firstBlock || firstBlock.type !== "heading" || firstBlock.depth !== 1) {
    return false;
  }
  return normalizeComparableTitle(firstBlock.text) === title;
}

/**
 * Builds render segments + outline in a single pass. The persisted markdown is
 * never mutated — a duplicated leading H1 is skipped at render time only.
 */
export function buildMarkdownDocumentModel(
  markdown: string,
  options: { documentTitle?: string } = {},
): MarkdownDocumentModel {
  const tokens = marked
    .lexer(String(markdown || ""), MARKDOWN_PARSE_OPTIONS)
    .slice();

  const title = normalizeComparableTitle(options.documentTitle ?? "");
  const firstBlockIndex = tokens.findIndex((token) => token.type !== "space");
  const firstBlock = firstBlockIndex >= 0 ? tokens[firstBlockIndex] : undefined;
  if (
    title &&
    firstBlock &&
    firstBlock.type === "heading" &&
    firstBlock.depth === 1 &&
    normalizeComparableTitle(firstBlock.text) === title
  ) {
    tokens.splice(firstBlockIndex, 1);
  }

  const slugCounts = new Map<string, number>();
  const headingIds: string[] = [];
  const outline: MarkdownDocumentOutlineItem[] = [];
  for (const token of tokens) {
    if (token.type !== "heading") continue;
    const heading = token as Tokens.Heading;
    const base = markdownHeadingSlug(heading.text);
    const count = (slugCounts.get(base) ?? 0) + 1;
    slugCounts.set(base, count);
    const id = count === 1 ? base : `${base}-${count}`;
    headingIds.push(id);
    const text = plainTextFromInlineMarkdown(heading.text);
    if (heading.depth >= 2) {
      outline.push({ id, depth: heading.depth, text });
    }
  }

  const pendingIds = [...headingIds];
  const renderer = new Renderer();
  renderer.heading = function heading(
    this: Renderer,
    { tokens: inlineTokens, depth }: Tokens.Heading,
  ) {
    const text = this.parser.parseInline(inlineTokens);
    const id = pendingIds.length > 0 ? pendingIds.shift() : undefined;
    const idAttr = id ? ` id="${id}"` : "";
    return `<h${depth}${idAttr}>${text}</h${depth}>\n`;
  };

  const segments: MarkdownDocumentSegment[] = [];
  let markdownRaw = "";
  const flushMarkdown = () => {
    const raw = markdownRaw;
    markdownRaw = "";
    if (!raw.trim()) return;
    const html = stripDangerousRichTextTags(
      marked.parse(raw, {
        ...MARKDOWN_PARSE_OPTIONS,
        async: false,
        renderer,
      }) as string,
    );
    segments.push({ type: "markdown", html });
  };

  for (const token of tokens as Token[]) {
    if (token.type === "code") {
      flushMarkdown();
      const code = token as Tokens.Code;
      const lang = (code.lang || "").trim().toLowerCase();
      if (lang === MERMAID_LANG) {
        segments.push({ type: "mermaid", code: code.text });
      } else {
        segments.push({ type: "code", lang: code.lang || "", code: code.text });
      }
      continue;
    }
    markdownRaw += token.raw;
  }
  flushMarkdown();

  return { segments, outline };
}
