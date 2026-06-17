import { readFileSync, existsSync } from "node:fs";

import { describe, expect, it } from "vitest";

import { buildAssistantContentSegments } from "./message/assistantContentSegments";

const LIVE_FIXTURE = "/tmp/analyser_meta.json";

describe("presentationStackBlueprint live fixture", () => {
  it.skipIf(!existsSync(LIVE_FIXTURE))(
    "ordena ficha → destaques → roteiro → árvore → pontos (API real)",
    () => {
      const raw = JSON.parse(readFileSync(LIVE_FIXTURE, "utf8")) as {
        content?: string;
        toolCalls?: unknown[];
      };

      const segments = buildAssistantContentSegments(
        raw.content || "",
        raw.toolCalls as never,
      );

      const indexOf = (predicate: (segment: (typeof segments)[number]) => boolean) =>
        segments.findIndex(predicate);

      const profileIndex = indexOf(
        (segment) =>
          segment.kind === "table" &&
          String(segment.presentation.title || "").startsWith("Produto "),
      );
      const destaqueIndex = indexOf(
        (segment) =>
          segment.kind === "markdown" &&
          segment.markdown.includes("Estrutura com 6 item"),
      );
      const roteiroIndex = indexOf(
        (segment) =>
          segment.kind === "table" &&
          String(segment.presentation.title || "").includes("Roteiro"),
      );
      const treeIndex = indexOf((segment) => segment.kind === "tree");
      const pontosIndex = indexOf(
        (segment) =>
          segment.kind === "markdown" &&
          segment.markdown.includes("1. Cadastro com indicador"),
      );

      expect(profileIndex).toBeGreaterThanOrEqual(0);
      expect(destaqueIndex).toBeGreaterThan(profileIndex);
      expect(roteiroIndex).toBeGreaterThan(destaqueIndex);
      expect(treeIndex).toBeGreaterThan(roteiroIndex);
      expect(pontosIndex).toBeGreaterThan(treeIndex);

      const markerLeak = segments.some(
        (segment) =>
          segment.kind === "markdown" && /\[\[(?:arvore|tree)]]/i.test(segment.markdown),
      );

      expect(markerLeak).toBe(false);
    },
  );
});
