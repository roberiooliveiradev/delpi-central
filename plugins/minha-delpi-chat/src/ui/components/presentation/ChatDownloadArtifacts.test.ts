import { beforeEach, describe, expect, it, vi } from "vitest";

import { getDownloadArtifactsFromToolCalls } from "./presentationMetadataReaders";
import { collectVisualSegments } from "./segmentBuilders/visualSegmentCollector";

describe("downloadArtifacts presentation", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("lê downloadArtifacts do metadata da tool call", () => {
    const artifacts = getDownloadArtifactsFromToolCalls([
      {
        name: "execute_external_action",
        metadata: {
          downloadArtifacts: [
            {
              href: "/apps/api-delpi/products/90261757/structure/excel?format=xlsx",
              filename: "Estrutura_90261757.xlsx",
              label: "Baixar Estrutura_90261757.xlsx",
            },
          ],
        },
      },
    ]);

    expect(artifacts).toHaveLength(1);
    expect(artifacts[0]?.filename).toBe("Estrutura_90261757.xlsx");
    expect(artifacts[0]?.href).toContain("/structure/excel");
  });

  it("coleta segmento download quando renderPlan permite", () => {
    const segments = collectVisualSegments([
      {
        name: "execute_external_action",
        metadata: {
          downloadArtifacts: [
            {
              href: "/apps/api-delpi/products/90261757/structure/excel?format=xlsx",
              filename: "Estrutura_90261757.xlsx",
              label: "Baixar planilha",
            },
          ],
          renderPlan: {
            version: 1,
            layoutMode: "stack",
            segments: [
              { kind: "markdown", slot: "lead", source: "textPresentation" },
              { kind: "download", slot: "artifacts", source: "downloadArtifacts" },
            ],
          },
        },
      },
    ]);

    expect(segments.some((segment) => segment.kind === "download")).toBe(true);
    const download = segments.find((segment) => segment.kind === "download");

    expect(download?.kind === "download" && download.artifacts[0]?.filename).toBe(
      "Estrutura_90261757.xlsx",
    );
  });
});
