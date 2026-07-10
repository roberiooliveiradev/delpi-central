import {
  joinContentLinesToRuns,
  splitContentRunsIntoLines,
} from "./comunicadoContentList";
import { plainTextFromContentRuns } from "./comunicadoContentRuns";
import { renderContentRunsHtml } from "./comunicadoContentRunEditing";
import type { ComunicadoContentRun } from "./comunicadoTypes";

const URL_LIKE_PATTERN = /^(https?:\/\/|mailto:|tel:|www\.)/i;

export function isLikelyExternalUrl(value: string): boolean {
  const trimmed = value.trim();
  if (!trimmed) return false;
  return URL_LIKE_PATTERN.test(trimmed) || /^[^\s]+\.[^\s]{2,}/.test(trimmed);
}

export function normalizeHrefInput(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (/^www\./i.test(trimmed)) return `https://${trimmed}`;
  return trimmed;
}

/** Inclui o endereço do link como última linha editável no palco (Canva/PPT). */
export function appendHrefLineToRuns(
  runs: ComunicadoContentRun[],
  href: string | undefined,
): ComunicadoContentRun[] {
  const trimmed = href?.trim();
  if (!trimmed) return runs;
  const plain = plainTextFromContentRuns(runs);
  if (plain.includes(trimmed)) return runs;
  const lines = splitContentRunsIntoLines(runs);
  const lastLine = lines[lines.length - 1];
  const lastText = plainTextFromContentRuns(lastLine?.runs ?? [{ text: "" }]);
  if (!lastText.trim()) {
    const nextLast = {
      ...lastLine,
      runs: [{ text: trimmed }],
    };
    return joinContentLinesToRuns([...lines.slice(0, -1), nextLast]);
  }
  return joinContentLinesToRuns([
    ...lines,
    { runs: [{ text: trimmed }], listType: undefined, namedStyle: undefined },
  ]);
}

/** Separa linhas URL (link do bloco) do texto exibido ao salvar. */
export function partitionTextBlockRunsAndHref(runs: ComunicadoContentRun[]): {
  runs: ComunicadoContentRun[];
  href?: string;
} {
  const lines = splitContentRunsIntoLines(runs);
  let href: string | undefined;
  const contentLines = [];

  for (const line of lines) {
    const text = plainTextFromContentRuns(line.runs).trim();
    if (text && isLikelyExternalUrl(text)) {
      href = normalizeHrefInput(text);
      continue;
    }
    contentLines.push(line);
  }

  if (contentLines.length === 0) {
    return { runs: [{ text: "" }], href };
  }

  return {
    runs: joinContentLinesToRuns(contentLines),
    href,
  };
}

export function hrefLineStyle(): { color: string; textDecoration: string } {
  return {
    color: "#60a5fa",
    textDecoration: "underline",
  };
}

/** Render do editor com linhas URL estilizadas como link no mesmo componente. */
export function renderTextBlockEditorHtml(
  runs: ComunicadoContentRun[],
  options?: { fontScale?: number },
): string {
  const lines = splitContentRunsIntoLines(runs);
  return lines
    .map((line) => {
      const text = plainTextFromContentRuns(line.runs).trim();
      const lineRuns = joinContentLinesToRuns([line]);
      let html = renderContentRunsHtml(lineRuns, options);
      if (!html.includes("data-comunicado-line")) {
        html = `<div data-comunicado-line="">${html || "<br>"}</div>`;
      }
      if (text && isLikelyExternalUrl(text)) {
        return html.replace(
          'data-comunicado-line=""',
          'data-comunicado-line="" data-comunicado-link-line="" class="td-composer__text-href-line"',
        );
      }
      return html;
    })
    .join("");
}
