import { mermaidClassDefLines, mermaidHighlightClassDefLines, wrapMermaidLabelText } from "./bpmnMermaidMapping";
import { MERMAID_LANE_LABEL_WRAPPING_WIDTH } from "./mermaidPreviewConfig";

const CLASS_DEF_LINE = /^\s*classDef\s+/;
const SUBGRAPH_LABEL_LINE = /^\s*subgraph\s+(\S+)\s+\["([^"]*)"\]\s*$/;

function collectUsedBpmnClasses(code: string): Set<string> {
  const used = new Set<string>();
  for (const match of code.matchAll(/:::(\w+)/g)) {
    used.add(match[1]);
  }
  return used;
}

function collectHighlightTokens(code: string): Set<string> {
  const highlights = new Set<string>();
  for (const match of code.matchAll(/:::highlight_(\w+)/g)) {
    highlights.add(match[1]);
  }
  return highlights;
}

/** Reaplica classDef conforme tema antes do preview Mermaid (export permanece em paleta clara). */
export function applyMermaidPreviewTheme(code: string, isDark: boolean): string {
  const trimmed = String(code || "").trim();
  if (!trimmed) return trimmed;

  const bodyLines = trimmed.split("\n").flatMap((line) => {
    if (CLASS_DEF_LINE.test(line)) return [];
    const subgraphMatch = line.match(SUBGRAPH_LABEL_LINE);
    if (!subgraphMatch) return [line];
    const [, subgraphId, rawLabel] = subgraphMatch;
    const normalized = rawLabel.replace(/<br\s*\/?>/gi, " ").replace(/\s+/g, " ").trim();
    const wrapped = wrapMermaidLabelText(normalized, MERMAID_LANE_LABEL_WRAPPING_WIDTH);
    return [`    subgraph ${subgraphId} ["${wrapped}"]`];
  });

  const usedClasses = collectUsedBpmnClasses(trimmed);
  const highlights = collectHighlightTokens(trimmed);
  const classDefLines = mermaidClassDefLines(usedClasses, isDark ? "dark" : "light");
  const highlightLines = mermaidHighlightClassDefLines(highlights, isDark ? "dark" : "light");

  return [...bodyLines, ...classDefLines, ...highlightLines].join("\n");
}
