/**
 * Markdown authoring helpers for the Process Documentation editor.
 * Toolbar actions only insert markdown — `content_md` stays canonical text.
 */

export type MarkdownToolbarAction =
  | "heading"
  | "bold"
  | "italic"
  | "link"
  | "list"
  | "checklist"
  | "quote"
  | "table"
  | "code"
  | "mermaid";

export type MarkdownInsertResult = {
  next: string;
  selectionStart: number;
  selectionEnd: number;
};

const INLINE_WRAP: Partial<
  Record<MarkdownToolbarAction, { before: string; after: string; placeholder: string }>
> = {
  bold: { before: "**", after: "**", placeholder: "texto em negrito" },
  italic: { before: "*", after: "*", placeholder: "texto em itálico" },
  link: { before: "[", after: "](https://)", placeholder: "texto do link" },
};

const LINE_PREFIX: Partial<Record<MarkdownToolbarAction, string>> = {
  heading: "## ",
  list: "- ",
  checklist: "- [ ] ",
  quote: "> ",
};

const BLOCK_TEMPLATES: Partial<Record<MarkdownToolbarAction, string>> = {
  table: "| Coluna | Coluna |\n|---|---|\n| valor | valor |",
  code: "```\ncódigo\n```",
  mermaid: "```mermaid\nflowchart TD\n  A[Início] --> B[Etapa]\n```",
};

function surroundWithBlankLines(source: string, start: number, end: number) {
  const before = source.slice(0, start);
  const after = source.slice(end);
  const needsBefore = before.length > 0 && !before.endsWith("\n\n");
  const needsAfter = after.length > 0 && !after.startsWith("\n");
  return {
    prefix: needsBefore ? (before.endsWith("\n") ? "\n" : "\n\n") : "",
    suffix: needsAfter ? "\n\n" : "",
  };
}

export function applyMarkdownToolbarAction(
  source: string,
  selectionStart: number,
  selectionEnd: number,
  action: MarkdownToolbarAction,
): MarkdownInsertResult {
  const start = Math.min(selectionStart, selectionEnd);
  const end = Math.max(selectionStart, selectionEnd);
  const selected = source.slice(start, end);

  const inline = INLINE_WRAP[action];
  if (inline) {
    const inner = selected || inline.placeholder;
    const next =
      source.slice(0, start) + inline.before + inner + inline.after + source.slice(end);
    const selStart = start + inline.before.length;
    return { next, selectionStart: selStart, selectionEnd: selStart + inner.length };
  }

  const prefix = LINE_PREFIX[action];
  if (prefix !== undefined) {
    const lineStart = source.lastIndexOf("\n", start - 1) + 1;
    const lineEnd = source.indexOf("\n", end);
    const blockEnd = lineEnd === -1 ? source.length : lineEnd;
    const block = source.slice(lineStart, blockEnd);
    const prefixed = block
      .split("\n")
      .map((line) => (line.trim() ? `${prefix}${line}` : line))
      .join("\n");
    const next = source.slice(0, lineStart) + prefixed + source.slice(blockEnd);
    const cursor = lineStart + prefixed.length;
    return { next, selectionStart: cursor, selectionEnd: cursor };
  }

  const template = BLOCK_TEMPLATES[action];
  if (template) {
    const { prefix: padBefore, suffix: padAfter } = surroundWithBlankLines(
      source,
      start,
      end,
    );
    const inserted = `${padBefore}${template}${padAfter}`;
    const next = source.slice(0, start) + inserted + source.slice(end);
    const cursor = start + padBefore.length + template.length;
    return { next, selectionStart: cursor, selectionEnd: cursor };
  }

  return { next: source, selectionStart: start, selectionEnd: end };
}
