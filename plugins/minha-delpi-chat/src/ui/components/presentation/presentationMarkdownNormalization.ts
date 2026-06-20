import type { ChatPresentation, ChatToolCall } from "../../../data/api/chatTypes";

export function isLlmProseDecoupledMetadata(
  metadata: Record<string, unknown> | null | undefined,
): boolean {
  if (!metadata || typeof metadata !== "object") {
    return false;
  }

  if (metadata.llmProseDecoupled === true) {
    return true;
  }

  const decision = metadata.presentationDecision;

  if (decision && typeof decision === "object") {
    const proseSource = String(
      (decision as Record<string, unknown>).proseSource || "",
    )
      .trim()
      .toLowerCase();

    if (proseSource === "llm") {
      return true;
    }
  }

  return String(metadata.proseDeliveryMode || "").trim().toLowerCase() === "llm";
}

export function isLlmProseDecoupledFromToolCalls(toolCalls?: ChatToolCall[]): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const metadata = toolCall.metadata as Record<string, unknown> | undefined;

    if (metadata?.ok === false) {
      continue;
    }

    if (isLlmProseDecoupledMetadata(metadata)) {
      return true;
    }
  }

  return false;
}

export function resolveLeadMarkdownSource(
  metadata: Record<string, unknown>,
  commentary: string,
): "assistantMessage" | "textPresentation" {
  if (isLlmProseDecoupledMetadata(metadata)) {
    return "assistantMessage";
  }

  const textPresentation = metadata.textPresentation;

  if (
    textPresentation &&
    typeof textPresentation === "object" &&
    String((textPresentation as { markdown?: string }).markdown || "").trim()
  ) {
    return "textPresentation";
  }

  if (String(commentary || "").trim()) {
    return "assistantMessage";
  }

  return "textPresentation";
}

export function getTextMarkdownFromToolCalls(toolCalls?: ChatToolCall[]): string {
  if (!Array.isArray(toolCalls)) {
    return "";
  }

  if (isLlmProseDecoupledFromToolCalls(toolCalls)) {
    return "";
  }

  const sections: string[] = [];

  for (const toolCall of toolCalls) {
    const textPresentation = (toolCall.metadata as Record<string, unknown>)?.textPresentation;

    if (
      textPresentation &&
      typeof textPresentation === "object" &&
      (textPresentation as { type?: string }).type === "markdown"
    ) {
      const markdown = (textPresentation as { markdown?: string }).markdown;

      if (typeof markdown === "string" && markdown.trim()) {
        sections.push(markdown.trim());
      }
    }
  }

  if (sections.length > 1) {
    return sections.join("\n\n");
  }

  if (sections.length === 1) {
    return sections[0];
  }

  for (const toolCall of toolCalls) {
    const textPresentation = (toolCall.metadata as Record<string, unknown>)?.textPresentation;

    if (
      textPresentation &&
      typeof textPresentation === "object" &&
      (textPresentation as { type?: string }).type === "markdown"
    ) {
      const markdown = (textPresentation as { markdown?: string }).markdown;

      if (typeof markdown === "string" && markdown.trim()) {
        return markdown.trim();
      }
    }

    const presentation = toolCall.metadata?.presentation;

    if (
      presentation &&
      typeof presentation === "object" &&
      (presentation as { type?: string }).type === "markdown"
    ) {
      const markdown = (presentation as { markdown?: string }).markdown;

      if (typeof markdown === "string" && markdown.trim()) {
        return markdown.trim();
      }
    }
  }

  return "";
}

function escapeMarkdownCell(value: unknown): string {
  return String(value ?? "")
    .replace(/\|/g, "\\|")
    .replace(/\n/g, " ");
}
export function tablePresentationToMarkdown(
  presentation: Extract<ChatPresentation, { type: "table" }>,
  options?: { includeTitle?: boolean },
): string {
  const { title, columns, rows } = presentation;
  const includeTitle = options?.includeTitle !== false;

  if (!columns.length) {
    return includeTitle && title ? `### ${title}` : "";
  }

  const header = columns.map((column) => column.label).join(" | ");
  const separator = columns.map(() => "---").join(" | ");
  const body = rows.map((row) =>
    columns.map((column) => escapeMarkdownCell(row[column.key])).join(" | "),
  );

  const tableLines = [
    `| ${header} |`,
    `| ${separator} |`,
    ...body.map((line) => `| ${line} |`),
  ];

  if (includeTitle && title) {
    return [`### ${title}`, "", ...tableLines].join("\n");
  }

  return tableLines.join("\n");
}

export function stripLeadingMarkdownTitle(markdown: string, title: string): string {
  const normalizedTitle = title.trim();

  if (!normalizedTitle) {
    return markdown.trim();
  }

  const lines = markdown.split("\n");
  const firstNonEmpty = lines.findIndex((line) => line.trim());

  if (firstNonEmpty === -1) {
    return "";
  }

  const heading = lines[firstNonEmpty].trim();

  if (
    heading === `### ${normalizedTitle}` ||
    heading === `## ${normalizedTitle}` ||
    heading === `# ${normalizedTitle}` ||
    heading === normalizedTitle
  ) {
    return lines
      .slice(firstNonEmpty + 1)
      .join("\n")
      .trim();
  }

  return markdown.trim();
}
export function hasDisplayableRichText(text: string | null | undefined): boolean {
  return String(text || "").trim().length > 0;
}
export function stripRedundantInspectionDumpFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();

    if (
      trimmed.startsWith("- Product=")
      || trimmed.includes("Qp6=[")
      || trimmed.includes("Qp7=[")
      || trimmed.includes("QP6_PRODUT")
    ) {
      continue;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

/** Remove tabela Campo/Valor duplicada quando `tablePresentation` já exibe o cadastro. */
export function stripRedundantProfileTableFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];
  let skipping = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (
      !skipping &&
      /^\|\s*(Campo|campo)\s*\|/i.test(trimmed) &&
      /\bValor\b/i.test(trimmed)
    ) {
      skipping = true;
      continue;
    }

    if (skipping) {
      if (trimmed.startsWith("|")) {
        continue;
      }

      skipping = false;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

/** Remove tabela markdown do roteiro quando `tablePresentation` já exibe o componente nativo. */
export function stripRedundantGuideTableFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];
  let skipping = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (!skipping && /^\*\*Roteiro de produção\*\*$/i.test(trimmed)) {
      skipping = true;
      continue;
    }

    if (skipping) {
      if (
        trimmed.startsWith("|") ||
        trimmed === "" ||
        /^Inspeção:/i.test(trimmed)
      ) {
        if (/^Inspeção:/i.test(trimmed)) {
          skipping = false;
          result.push(line);
        }

        continue;
      }

      skipping = false;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

/** Remove blocos markdown de inspeção quando há tabela nativa no metadata. */
export function stripRedundantInspectionFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];
  let skipping = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (!skipping && /^\*\*Plano de inspeção\*\*$/i.test(trimmed)) {
      skipping = true;
      continue;
    }

    if (skipping) {
      if (
        trimmed.startsWith("|") ||
        trimmed === "" ||
        /^\*(Ensaios|Componentes referenciados)/i.test(trimmed) ||
        /^\*\*Destaques\*\*$/i.test(trimmed) ||
        /^\*\*Pontos de atenção/i.test(trimmed)
      ) {
        if (
          /^\*\*Destaques\*\*$/i.test(trimmed) ||
          /^\*\*Pontos de atenção/i.test(trimmed)
        ) {
          skipping = false;
          result.push(line);
        }

        continue;
      }

      skipping = false;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

export function stripRedundantStructureFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];
  let skipping = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (
      !skipping &&
      (trimmed.startsWith("**Estrutura do produto") ||
        trimmed === "**Produto pai**" ||
        trimmed === "**Componentes nível 1**" ||
        trimmed === "**Estrutura detalhada**")
    ) {
      skipping = true;
      continue;
    }

    if (skipping) {
      if (trimmed.startsWith("**Insights**")) {
        skipping = false;
        result.push(line);
      }

      continue;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

export function stripRedundantHierarchyListFromMarkdown(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();

    if (
      trimmed.startsWith("**") &&
      trimmed.includes("—") &&
      (trimmed.includes("| Qtd:") || trimmed.includes("Qtd:"))
    ) {
      continue;
    }

    if (/^Total encontrado:/i.test(trimmed)) {
      continue;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}
export function stripMarkdownGfmTablesFromCommentary(markdown: string): string {
  const lines = markdown.split("\n");
  const result: string[] = [];
  let skipping = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (!skipping && trimmed.startsWith("|") && trimmed.includes("|")) {
      skipping = true;
      continue;
    }

    if (skipping) {
      if (trimmed.startsWith("|") || trimmed === "") {
        continue;
      }

      skipping = false;
    }

    result.push(line);
  }

  return result.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}
export function stripCompositionCodeFenceFromMarkdown(markdown: string): string {
  const withSection = markdown.replace(
    /(?:^|\n)\s*\*\*Composição\*\*\s*\n+```[\w-]*\s*\n[\s\S]*?\n```/gi,
    "",
  );

  return withSection.replace(/(?:^|\n)\s*```text\s*\n[\s\S]*?\n```/gi, "").trim();
}

export function stripChartMarkdownFallbackFromMarkdown(markdown: string): string {
  return markdown
    .replace(
      /(?:^|\n)\s*\*\*[^*]+\*\*\s*\n+_Dados do gráfico[\s\S]*?(?=\n\*\*[^*]+\*\*|\n#{1,3} |\n<!-- section:|\Z)/gi,
      "",
    )
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
export function stripCoverageNoticeFromMarkdown(markdown: string): string {
  const trimmed = String(markdown || "").trim();

  if (!trimmed) {
    return "";
  }

  const coverageBlockPattern =
    /(?:^|\n\n)> \*\*Cobertura dos dados:\*\*[^\n]*(?:\n> [^\n]*)*/gu;

  return trimmed.replace(coverageBlockPattern, "").replace(/\n{3,}/g, "\n\n").trim();
}
