import { describe, expect, it } from "vitest";

import {
  buildAssistantContentSegments,
  dedupeSqlFencesInMarkdown,
  parseMarkdownAndCodeSegments,
} from "./assistantContentSegments";

describe("assistantContentSegments", () => {
  it("remove blocos SQL duplicados", () => {
    const input =
      "```sql\nSELECT A1_COD FROM SA1010\n```\n\n```sql\nSELECT A1_COD FROM SA1010\n```";

    expect(dedupeSqlFencesInMarkdown(input)).toBe(
      "```sql\nSELECT A1_COD FROM SA1010\n```",
    );
  });

  it("separa texto explicativo e bloco SQL", () => {
    const segments = parseMarkdownAndCodeSegments(
      "Segue a consulta:\n\n```sql\nSELECT A1_COD, A1_NOME FROM SA1010\n```",
    );

    expect(segments).toHaveLength(2);
    expect(segments[0]).toMatchObject({ kind: "markdown" });
    expect(segments[1]).toMatchObject({ kind: "code", language: "sql" });
  });

  it("insere marcador [[table]] no meio do texto", () => {
    const segments = buildAssistantContentSegments(
      "Resumo inicial.\n\n[[table]]\n\nConclusão.",
      [
        {
          name: "execute_external_action",
          metadata: {
            presentation: {
              type: "table",
              title: "Estoque",
              columns: [{ key: "branch", label: "Filial" }],
              rows: [{ branch: "01" }],
            },
          },
        },
      ],
    );

    expect(segments.some((item) => item.kind === "markdown")).toBe(true);
    expect(segments.some((item) => item.kind === "table")).toBe(true);
  });
});
