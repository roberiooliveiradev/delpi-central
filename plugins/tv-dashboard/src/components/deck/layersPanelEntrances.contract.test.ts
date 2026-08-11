import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("entradas e ordem — contrato de source", () => {
  it("prévia aplica animate-entrances; editor não", () => {
    const preview = readFileSync(join(here, "../../presentation/PresentationPreview.tsx"), "utf8");
    const composer = readFileSync(join(here, "../ComunicadoComposer.tsx"), "utf8");
    expect(preview).toContain("presentationStageEntranceClass");
    expect(composer).not.toContain("tdp-stage--animate-entrances");
    expect(composer).not.toContain("presentationStageEntranceClass");
  });

  it("Sequenciar/Limpar usam um updateBlocksAtomically", () => {
    const panel = readFileSync(join(here, "ComunicadoLayersPanel.tsx"), "utf8");
    expect(panel).toContain("updateBlocksAtomically");
    expect(panel).not.toMatch(/updateBlock\(id,\s*\{\s*animations/);
  });
});
