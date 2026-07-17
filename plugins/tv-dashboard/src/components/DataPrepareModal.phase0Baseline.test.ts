import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const SOURCE = readFileSync(
  resolve(process.cwd(), "src/components/DataPrepareModal.tsx"),
  "utf8",
);
const WORKBENCH = readFileSync(
  resolve(process.cwd(), "src/features/data-query/ui/DataPrepareModal.tsx"),
  "utf8",
);

describe("DataPrepareModal — baseline transacional da Fase 0", () => {
  it("mantém o legado isolado e o compositor escolhe capability server-side", () => {
    expect(SOURCE).toMatch(/function LegacyDataPrepareModal/);
    expect(SOURCE).toMatch(/canUseMWorkbench\(capabilities\)/);
    expect(SOURCE).toMatch(/<DataQueryWorkbenchModal/);
  });

  it("Cancelar só fecha e Aplicar usa o comando atômico", () => {
    expect(WORKBENCH).toMatch(/onClick=\{onClose\}[\s\S]*Cancelar/);
    expect(WORKBENCH).toMatch(/workbench\.apply\(updateBlocksAtomically\)/);
    expect(WORKBENCH).not.toMatch(/updateBlock\(/);
  });

  it("selecionar coluna não troca a seleção global nem fecha o modal", () => {
    expect(SOURCE).toMatch(/aria-selected=\{isActiveCol\}[\s\S]*toggleColumn\(col\)/);
    expect(SOURCE).not.toMatch(/selectChartPart/);
    expect(SOURCE).not.toMatch(/title=\{H\.(modal|grid)\}/);
  });
});
