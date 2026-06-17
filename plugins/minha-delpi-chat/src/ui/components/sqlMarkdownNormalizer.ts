import type { AssistantContentSegment } from "./message/assistantContentTypes";
import { proseChunksSimilar } from "./segmentDedupe";

export const SQL_FENCE_RE = /```sql\s*([\s\S]*?)```/gi;

export const SQL_AUTHORING_INTRO_RE =
  /Segue a consulta em SQL\s*\(somente leitura[\s\S]*?conforme o ambiente:\s*/gi;

const SQL_AUTHORING_INTRO =
  "Segue a consulta em SQL (somente leitura, sem executar no sistema). " +
  "Ajuste sufixo de tabela (ex.: SA1010) conforme o ambiente:";

function extractSqlFromFence(fence: string): string {
  return fence
    .replace(/^```sql\s*/i, "")
    .replace(/\s*```\s*$/i, "")
    .trim();
}

function stripRedundantSqlTailProse(content: string): string {
  const pattern = /```sql\s*[\s\S]*?```/gi;
  const blocks = [...content.matchAll(pattern)];

  if (!blocks.length) {
    return content;
  }

  const primary = blocks[0];
  const start = primary.index ?? 0;
  const end = start + primary[0].length;
  const before = content.slice(0, start).trim();
  const tail = content.slice(end).replace(pattern, "").trim();

  if (!tail) {
    return content.slice(0, end).trim();
  }

  if (before && proseChunksSimilar(before, tail)) {
    return content.slice(0, end).trim();
  }

  const paragraphs = tail
    .split(/\n\s*\n/)
    .map((part) => part.trim())
    .filter(Boolean);
  const kept: string[] = [];

  for (const paragraph of paragraphs) {
    if (before && proseChunksSimilar(before, paragraph)) {
      continue;
    }

    if (kept.length && proseChunksSimilar(kept[kept.length - 1], paragraph)) {
      continue;
    }

    kept.push(paragraph);
  }

  if (!kept.length) {
    return content.slice(0, end).trim();
  }

  return `${content.slice(0, end).trim()}\n\n${kept.join("\n\n")}`.trim();
}

function stripDuplicateSqlAuthoringIntro(content: string): string {
  const matches = [...content.matchAll(SQL_AUTHORING_INTRO_RE)];

  if (matches.length <= 1) {
    return content.trim();
  }

  let seen = false;

  return content
    .replace(SQL_AUTHORING_INTRO_RE, (match) => {
      if (!seen) {
        seen = true;
        return match;
      }

      return "";
    })
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function collectUniqueAuthoringProse(content: string): string[] {
  const fragments: string[] = [];
  let cursor = 0;

  for (const match of content.matchAll(SQL_FENCE_RE)) {
    const index = match.index ?? 0;
    fragments.push(content.slice(cursor, index));
    cursor = index + match[0].length;
  }

  fragments.push(content.slice(cursor));

  const paragraphs = fragments.flatMap((fragment) =>
    fragment
      .replace(SQL_AUTHORING_INTRO_RE, "\n")
      .split(/\n\s*\n/)
      .map((part) => part.trim())
      .filter(Boolean),
  );
  const kept: string[] = [];

  for (const paragraph of paragraphs) {
    if (proseChunksSimilar(SQL_AUTHORING_INTRO, paragraph)) {
      continue;
    }

    if (kept.length && proseChunksSimilar(kept[kept.length - 1], paragraph)) {
      continue;
    }

    kept.push(paragraph);
  }

  return kept;
}

function canonicalizeSqlAuthoringMarkdown(content: string): string {
  const blocks = [...content.matchAll(SQL_FENCE_RE)];

  if (!blocks.length) {
    return content.trim();
  }

  const sqlBody = blocks
    .map((block) => extractSqlFromFence(block[0]))
    .sort((left, right) => {
      const lineDelta = right.split("\n").length - left.split("\n").length;

      return lineDelta || right.length - left.length;
    })[0];

  if (!sqlBody) {
    return content.trim();
  }

  const firstIndex = blocks[0].index ?? 0;
  const beforeFirst = content.slice(0, firstIndex).trim();
  const customBefore = beforeFirst.replace(SQL_AUTHORING_INTRO_RE, "").trim();
  const paragraphs = collectUniqueAuthoringProse(content);
  const parts: string[] = [];

  if (customBefore.length >= 16) {
    parts.push(customBefore);
  } else {
    parts.push(SQL_AUTHORING_INTRO);
  }

  parts.push(`\`\`\`sql\n${sqlBody}\n\`\`\``);

  for (const paragraph of paragraphs) {
    if (parts.length && proseChunksSimilar(parts[0], paragraph)) {
      continue;
    }

    parts.push(paragraph);
  }

  return parts.join("\n\n").trim();
}

export function dedupeSqlFencesInMarkdown(content: string): string {
  const matches = [...content.matchAll(SQL_FENCE_RE)];

  if (!matches.length) {
    return content.trim();
  }

  const merged =
    matches.length > 1 ? canonicalizeSqlAuthoringMarkdown(content) : content.trim();

  return stripRedundantSqlTailProse(stripDuplicateSqlAuthoringIntro(merged));
}

export function parseMarkdownAndCodeSegments(content: string): AssistantContentSegment[] {
  const normalized = dedupeSqlFencesInMarkdown(content);
  const segments: AssistantContentSegment[] = [];
  let lastIndex = 0;

  for (const match of normalized.matchAll(SQL_FENCE_RE)) {
    const index = match.index ?? 0;
    const prose = normalized.slice(lastIndex, index).trim();

    if (prose) {
      segments.push({ kind: "markdown", markdown: prose });
    }

    const code = String(match[1] || "").trim();

    if (code) {
      segments.push({ kind: "code", language: "sql", code });
    }

    lastIndex = index + match[0].length;
  }

  const tail = normalized.slice(lastIndex).trim();

  if (tail) {
    segments.push({ kind: "markdown", markdown: tail });
  }

  if (!segments.length && normalized) {
    segments.push({ kind: "markdown", markdown: normalized });
  }

  return segments;
}

export function filterRedundantSqlIntroSegments(
  textSegments: AssistantContentSegment[],
): AssistantContentSegment[] {
  const introOnly = (value: string) => {
    const normalized = value.trim();
    const withoutIntro = normalized.replace(SQL_AUTHORING_INTRO_RE, "").trim();

    return /segue a consulta em sql/i.test(normalized) && withoutIntro.length < 8;
  };

  const filtered = textSegments.filter((segment, index, list) => {
    if (segment.kind !== "markdown" || !introOnly(segment.markdown)) {
      return true;
    }

    const hasCodeAfter = list.slice(index + 1).some((item) => item.kind === "code");

    if (hasCodeAfter) {
      return false;
    }

    const earlierIntro = list
      .slice(0, index)
      .some((item) => item.kind === "markdown" && introOnly(item.markdown));

    return !earlierIntro;
  });

  const codeIndex = filtered.findIndex((item) => item.kind === "code");

  if (codeIndex < 0) {
    return filtered.length ? filtered : textSegments;
  }

  const beforeMarkdown = filtered
    .slice(0, codeIndex)
    .filter((item) => item.kind === "markdown")
    .map((item) => (item.kind === "markdown" ? item.markdown : ""))
    .join("\n\n");
  const dedupedAroundCode = filtered.filter((segment, index) => {
    if (segment.kind !== "markdown" || index <= codeIndex) {
      return true;
    }

    return !proseChunksSimilar(beforeMarkdown, segment.markdown);
  });

  return dedupedAroundCode.length ? dedupedAroundCode : textSegments;
}
